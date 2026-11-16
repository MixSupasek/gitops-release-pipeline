import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "v1"


class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            status, response = 200, {"status": "ok"}
        elif self.path == "/version":
            status, response = 200, {"version": VERSION}
        else:
            status, response = 404, {"error": "not found"}

        body = json.dumps(response).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), ApiHandler).serve_forever()