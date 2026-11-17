import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from cfguard.web import audit, make_handler


class WebTests(unittest.TestCase):
    def test_demo_results(self):
        self.assertEqual(audit("secure")["passed"], 4)
        self.assertEqual(audit("insecure")["passed"], 0)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            audit("../../secret")

    def test_http_audit_and_csrf(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler("test-token"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_port
            connection = HTTPConnection("127.0.0.1", port)
            connection.request("POST", "/api/audit", body=json.dumps({"mode": "secure"}),
                               headers={"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"})
            self.assertEqual(connection.getresponse().status, 403)
            connection.request("POST", "/api/audit", body=json.dumps({"mode": "secure"}),
                               headers={"Origin": f"http://127.0.0.1:{port}", "X-CSRF-Token": "test-token", "Content-Type": "application/json"})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["passed"], 4)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
