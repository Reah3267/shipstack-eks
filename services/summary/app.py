import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import URLError

TASKS_URL = os.getenv("TASKS_URL", "http://tasks:8000")

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            return self.reply(200, {"status": "ok", "service": "summary"})
        if self.path != "/summary":
            return self.reply(404, {"error": "not found"})
        try:
            with urlopen(TASKS_URL + "/tasks", timeout=3) as response:
                tasks = json.load(response)
            done = sum(t["completed"] for t in tasks)
            self.reply(200, {"total": len(tasks), "completed": done, "pending": len(tasks)-done})
        except (URLError, OSError, ValueError, KeyError, TypeError):
            self.reply(503, {"error": "task service unavailable"})

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8001"))), Handler)
    server.daemon_threads = True
    server.serve_forever()
