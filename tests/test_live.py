import json
import unittest
import urllib.error
from unittest.mock import patch

from cfguard.live import CloudflareAPIError, CloudflareClient, audit_live_ddos


ZONE = "a" * 32


class FakeClient:
    def __init__(self, *, proxied=True, no_dns=False, denied=False):
        self.proxied = proxied
        self.no_dns = no_dns
        self.denied = denied

    def get(self, suffix, *, optional=False):
        if suffix == "":
            return {"result": {"name": "example.com", "status": "active", "paused": False}}
        if self.denied:
            raise CloudflareAPIError("Cloudflare API returned HTTP 403", 403)
        if suffix.startswith("/rulesets/"):
            return {"result": {"rules": [{"enabled": True, "action": "managed_challenge"}]}}
        if suffix == "/bot_management":
            return {"result": {"fight_mode": True}}
        raise AssertionError(suffix)

    def dns_records(self):
        if self.denied:
            raise CloudflareAPIError("Cloudflare API returned HTTP 403", 403)
        return [] if self.no_dns else [{"name": "example.com", "type": "A", "proxied": self.proxied}]


class LiveAuditTests(unittest.TestCase):
    def test_real_zone_posture_passes_verifiable_checks(self):
        result = audit_live_ddos(ZONE, "token", client=FakeClient())
        self.assertEqual([item["status"] for item in result["checks"]],
                         ["PASS", "PASS", "PASS", "PASS", "PASS", "UNKNOWN"])
        self.assertNotIn("token", result["report"])

    def test_unproxied_host_is_a_failure(self):
        result = audit_live_ddos(ZONE, "token", client=FakeClient(proxied=False))
        self.assertEqual(result["checks"][1]["status"], "FAIL")
        self.assertEqual(result["checks"][2]["status"], "FAIL")

    def test_missing_dns_or_denied_access_is_unknown(self):
        missing = audit_live_ddos(ZONE, "token", client=FakeClient(no_dns=True))
        denied = audit_live_ddos(ZONE, "token", client=FakeClient(denied=True))
        self.assertEqual(missing["checks"][1]["status"], "UNKNOWN")
        self.assertEqual(denied["checks"][1]["status"], "UNKNOWN")
        self.assertEqual(denied["checks"][3]["status"], "UNKNOWN")

    def test_hostname_must_belong_to_zone(self):
        with self.assertRaises(ValueError):
            audit_live_ddos(ZONE, "token", ["other.com"], client=FakeClient())

    def test_client_paginates_dns_records(self):
        class Response:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, *_):
                return json.dumps(self.payload).encode()

        def opener(request, timeout):
            page = 1 if "page=1" in request.full_url else 2
            return Response({"success": True, "result": [{"name": f"host{page}.example.com"}],
                             "result_info": {"total_pages": 2}})

        client = CloudflareClient(ZONE, "token", opener=opener)
        self.assertEqual(len(client.dns_records()), 2)

    def test_optional_404_and_required_403(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 404, "Not found", None, None)

        client = CloudflareClient(ZONE, "token", opener=opener)
        self.assertIsNone(client.get("/rulesets/phases/http_ratelimit/entrypoint", optional=True))
        with self.assertRaises(CloudflareAPIError):
            client.get("")


if __name__ == "__main__":
    unittest.main()
