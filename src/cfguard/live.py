"""Read-only DDoS posture audit of a real Cloudflare zone."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .cli import markdown_report


ZONE_ID = re.compile(r"^[0-9a-fA-F]{32}$")
WEB_TYPES = {"A", "AAAA", "CNAME"}
MITIGATING_ACTIONS = {"block", "challenge", "managed_challenge", "js_challenge"}


class CloudflareAPIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class CloudflareClient:
    def __init__(self, zone_id: str, token: str, opener=None):
        if not ZONE_ID.fullmatch(zone_id or ""):
            raise ValueError("zone ID must be 32 hexadecimal characters")
        if not token:
            raise ValueError("CF_API_TOKEN is required")
        self.zone_id = zone_id
        self.token = token
        self.opener = opener or urllib.request.urlopen

    def get(self, suffix: str, *, optional: bool = False) -> dict | list | None:
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}{suffix}"
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"})
        try:
            with self.opener(request, timeout=10) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            error.close()
            if optional and error.code == 404:
                return None
            raise CloudflareAPIError(f"Cloudflare API returned HTTP {error.code}", error.code) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise CloudflareAPIError("Cloudflare API returned invalid JSON") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise CloudflareAPIError("Cloudflare API request failed") from error
        if not isinstance(payload, dict) or payload.get("success") is not True or "result" not in payload:
            raise CloudflareAPIError("Cloudflare API returned an invalid response")
        return payload

    def dns_records(self) -> list[dict]:
        records = []
        page = 1
        while True:
            payload = self.get(f"/dns_records?per_page=100&page={page}")
            batch = payload["result"]
            if not isinstance(batch, list):
                raise CloudflareAPIError("Cloudflare DNS response is not a list")
            records.extend(batch)
            info = payload.get("result_info") or {}
            pages = info.get("total_pages", 1)
            if not isinstance(pages, int) or pages < 1 or pages > 100:
                raise CloudflareAPIError("Cloudflare DNS pagination is invalid or too large")
            if page >= pages:
                return records
            page += 1


def finding(name: str, key: str, status: str, actual: str, expected: str) -> dict:
    return {"check": name, "setting": key, "status": status, "actual": actual, "expected": expected}


def audit_live_ddos(zone_id: str, token: str, hostnames: list[str] | None = None, client=None) -> dict:
    client = client or CloudflareClient(zone_id, token)
    zone = client.get("")["result"]
    if not isinstance(zone, dict) or not isinstance(zone.get("name"), str):
        raise CloudflareAPIError("Cloudflare zone response is incomplete")
    zone_name = zone["name"].lower().rstrip(".")
    hosts = [host.lower().rstrip(".") for host in (hostnames or [zone_name])]
    if any(not host or not (host == zone_name or host.endswith("." + zone_name)) for host in hosts):
        raise ValueError("hostnames must belong to the selected zone")

    active = zone.get("status") == "active" and zone.get("paused") is not True
    checks = [finding("Зона Cloudflare активна", "zone_status", "PASS" if active else "FAIL",
                      f"{zone.get('status', 'unknown')}; paused={zone.get('paused', 'unknown')}", "active; paused=false")]

    dns_ok = None
    try:
        records = client.dns_records()
        details = []
        statuses = []
        for host in hosts:
            matching = [record for record in records if isinstance(record, dict) and isinstance(record.get("name"), str)
                        and record["name"].lower().rstrip(".") == host and record.get("type") in WEB_TYPES]
            if not matching:
                details.append(f"{host}: no A/AAAA/CNAME record")
                statuses.append(None)
            else:
                proxied = all(record.get("proxied") is True for record in matching)
                details.append(f"{host}: {'proxied' if proxied else 'DNS only'}")
                statuses.append(proxied)
        dns_ok = all(status is True for status in statuses) if all(status is not None for status in statuses) else None
        dns_status = "PASS" if dns_ok is True else "FAIL" if dns_ok is False else "UNKNOWN"
        checks.append(finding("Веб-DNS проксируется", "dns_proxy", dns_status, "; ".join(details), "all selected web records proxied"))
    except CloudflareAPIError as error:
        checks.append(finding("Веб-DNS проксируется", "dns_proxy", "UNKNOWN", str(error), "DNS Read permission"))

    if active and dns_ok is True:
        edge_status, edge_actual = "PASS", "Cloudflare proxy path confirmed; mitigation inferred from product defaults"
    elif not active or dns_ok is False:
        edge_status, edge_actual = "FAIL", "traffic may bypass Cloudflare protection"
    else:
        edge_status, edge_actual = "UNKNOWN", "proxy path could not be confirmed"
    checks.append(finding("DDoS-защита на краю сети", "edge_ddos", edge_status, edge_actual, "active zone and proxied web traffic"))

    try:
        payload = client.get("/rulesets/phases/http_ratelimit/entrypoint", optional=True)
        config = {} if payload is None else payload.get("result")
        if not isinstance(config, dict):
            raise CloudflareAPIError("Cloudflare rate limit response is invalid")
        rules = config.get("rules", [])
        if not isinstance(rules, list):
            raise CloudflareAPIError("Cloudflare rate limit response is invalid")
        active_rules = [rule for rule in rules if isinstance(rule, dict) and rule.get("enabled", True) is not False
                        and rule.get("action") in MITIGATING_ACTIONS]
        checks.append(finding("Активное ограничение запросов", "rate_limit", "PASS" if active_rules else "WARN",
                              f"{len(active_rules)} active mitigating rule(s)", "at least one targeted rule; review its expression"))
    except CloudflareAPIError as error:
        checks.append(finding("Активное ограничение запросов", "rate_limit", "UNKNOWN", str(error), "Zone WAF Read permission"))

    try:
        payload = client.get("/bot_management", optional=True)
        config = {} if payload is None else payload.get("result", {})
        if not isinstance(config, dict):
            raise CloudflareAPIError("Cloudflare bot response is invalid")
        enabled = config.get("fight_mode") is True or config.get("sbfm_definitely_automated") in MITIGATING_ACTIONS
        checks.append(finding("Защита от ботов", "bot_management", "PASS" if enabled else "WARN",
                              "enabled" if enabled else "not enabled / not available", "review for browser traffic; APIs may need exceptions"))
    except CloudflareAPIError as error:
        checks.append(finding("Защита от ботов", "bot_management", "UNKNOWN", str(error), "Bot Management Read permission"))

    checks.append(finding("Изоляция origin", "origin_isolation", "UNKNOWN", "not verifiable from zone settings API",
                          "verify firewall, Tunnel, or authenticated origin access manually"))
    return {"source": f"Cloudflare API: {zone_name}", "checks": checks,
            "passed": sum(check["status"] == "PASS" for check in checks), "total": len(checks),
            "report": markdown_report(checks, f"Cloudflare API: {zone_name}")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Cloudflare DDoS posture audit")
    parser.add_argument("--zone-id", default=os.environ.get("CF_ZONE_ID", ""))
    parser.add_argument("--hostname", action="append", help="Web hostname to check; repeatable; defaults to zone apex")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_live_ddos(args.zone_id, os.environ.get("CF_API_TOKEN", ""), args.hostname)
        print(result["report"])
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(result["report"], encoding="utf-8")
        return 1 if any(check["status"] == "FAIL" for check in result["checks"]) else 0
    except (CloudflareAPIError, OSError, ValueError) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
