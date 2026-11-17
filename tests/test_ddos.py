import unittest
import tempfile
import json
from pathlib import Path

from cfguard.ddos import evaluate_ddos
from cfguard.demo import generate
from cfguard.limits import SlidingWindowLimiter
from cfguard.web import audit


class DDoSTests(unittest.TestCase):
    def test_safe_profile_and_missing_fields(self):
        self.assertEqual(audit("ddos_secure")["passed"], 5)
        self.assertEqual([r["status"] for r in evaluate_ddos({})], ["FAIL"] * 5)
        self.assertEqual(audit("ddos_insecure")["passed"], 1)

    def test_rate_limit_resets_after_window(self):
        limiter = SlidingWindowLimiter(maximum=2, window_seconds=60)
        self.assertTrue(limiter.allow("client", now=100))
        self.assertTrue(limiter.allow("client", now=101))
        self.assertFalse(limiter.allow("client", now=102))
        self.assertTrue(limiter.allow("client", now=161))

    def test_demo_evidence_is_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = generate(Path(directory))
            self.assertEqual(len(paths), 4)
            self.assertTrue(all(path.exists() and "Result:" in path.read_text() for path in paths))

    def test_public_demo_matches_evaluator(self):
        data = json.loads(Path("site/data.json").read_text(encoding="utf-8"))
        self.assertEqual(data, {mode: audit(mode) for mode in ("secure", "insecure", "ddos_secure", "ddos_insecure")})


if __name__ == "__main__":
    unittest.main()
