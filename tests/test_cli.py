import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cfguard.cli import evaluate, fetch_settings, main


class AuditTests(unittest.TestCase):
    def test_secure_baseline_passes(self):
        settings = {"always_use_https": "on", "ssl": "strict", "min_tls_version": "1.2", "tls_1_3": "on"}
        self.assertEqual([r["status"] for r in evaluate(settings)], ["PASS"] * 4)

    def test_insecure_and_missing_settings_fail_closed(self):
        self.assertEqual([r["status"] for r in evaluate({})], ["FAIL"] * 4)
        self.assertEqual(main(["--fixture", "fixtures/insecure.json"]), 1)

    def test_bad_fixture_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(["not an object"]))
            self.assertEqual(main(["--fixture", str(path)]), 2)

    def test_live_mode_requires_token(self):
        with patch.dict("os.environ", {"CF_API_TOKEN": ""}):
            self.assertEqual(main(["--zone-id", "example"]), 2)

    def test_api_result_must_match_setting(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, *_):
                return b'{"success":true,"result":{"id":"wrong","value":"on"}}'

        with patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaisesRegex(ValueError, "unexpected setting"):
                fetch_settings("zone", "token")


if __name__ == "__main__":
    unittest.main()
