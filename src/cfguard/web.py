"""Local-only web dashboard for the Cloudflare baseline auditor."""

import argparse
import json
import os
import secrets
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .cli import evaluate, fetch_settings, markdown_report
from .ddos import evaluate_ddos
from .limits import SlidingWindowLimiter


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "web"
FIXTURES = ROOT / "fixtures"
AUDIT_LIMITER = SlidingWindowLimiter(maximum=30, window_seconds=60)
AUDIT_SLOTS = threading.BoundedSemaphore(2)


def audit(mode: str, token: str = "", zone_id: str = "") -> dict:
    if mode in ("secure", "insecure", "ddos_secure", "ddos_insecure"):
        settings = json.loads((FIXTURES / f"{mode}.json").read_text(encoding="utf-8"))
        source = f"Demo: {mode}"
        checks = evaluate_ddos(settings) if mode.startswith("ddos_") else evaluate(settings)
    elif mode == "live":
        settings = fetch_settings(zone_id, token)
        source = "Cloudflare API"
        checks = evaluate(settings)
    else:
        raise ValueError("Unknown audit mode")
    return {
        "source": source,
        "checks": checks,
        "passed": sum(check["status"] == "PASS" for check in checks),
        "total": len(checks),
        "report": markdown_report(checks, source),
    }


def make_handler(csrf_token: str):
    class Handler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(5)

        def _valid_host(self) -> bool:
            host = self.headers.get("Host", "")
            return host in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: dict) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            if not self._valid_host():
                self._json(403, {"error": "Invalid host"})
                return
            path = urlsplit(self.path).path
            if path == "/api/status":
                self._json(200, {"live_ready": bool(os.environ.get("CF_API_TOKEN") and os.environ.get("CF_ZONE_ID")), "csrf": csrf_token})
                return
            files = {"/": ("index.html", "text/html; charset=utf-8"),
                     "/style.css": ("style.css", "text/css; charset=utf-8"),
                     "/app.js": ("app.js", "text/javascript; charset=utf-8")}
            if path not in files:
                self._json(404, {"error": "Not found"})
                return
            filename, content_type = files[path]
            self._send(200, (PUBLIC / filename).read_bytes(), content_type)

        def do_POST(self) -> None:
            if not self._valid_host() or urlsplit(self.path).path != "/api/audit":
                self._json(403, {"error": "Request rejected"})
                return
            origin = self.headers.get("Origin", "")
            if origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                self._json(403, {"error": "Invalid origin"})
                return
            if not secrets.compare_digest(self.headers.get("X-CSRF-Token", ""), csrf_token):
                self._json(403, {"error": "Invalid request token"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 1024:
                    raise ValueError("Invalid request size")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Invalid request body")
                mode = body.get("mode")
                if not AUDIT_LIMITER.allow(self.client_address[0]):
                    self._json(429, {"error": "Слишком много проверок. Повторите через минуту."})
                    return
                if not AUDIT_SLOTS.acquire(blocking=False):
                    self._json(429, {"error": "Проверки заняты. Повторите позже."})
                    return
                try:
                    result = audit(mode, os.environ.get("CF_API_TOKEN", ""), os.environ.get("CF_ZONE_ID", ""))
                    self._json(200, result)
                finally:
                    AUDIT_SLOTS.release()
            except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as error:
                self._json(400, {"error": str(error)})

        def log_message(self, format_string: str, *args) -> None:
            # Avoid recording request details or zone data in a local log.
            pass

    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Cloudflare Baseline Guard dashboard")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(secrets.token_urlsafe(32)))
    server.daemon_threads = True
    print(f"Open http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
