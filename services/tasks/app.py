import json
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TASKS = {}
LOCK = threading.Lock()

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
            return self.reply(200, {"status": "ok", "service": "tasks"})
        if self.path == "/tasks":
            with LOCK:
                result = [dict(t) for t in TASKS.values()]
            return self.reply(200, result)
        self.reply(404, {"error": "not found"})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 4096:
            raise ValueError("body must be between 1 and 4096 bytes")
        if self.headers.get_content_type() != "application/json":
            raise ValueError("use application/json")
        body = json.loads(self.rfile.read(length))
        if not isinstance(body, dict):
            raise ValueError("body must be an object")
        return body

    def do_POST(self):
        if self.path != "/tasks":
            return self.reply(404, {"error": "not found"})
        try:
            body = self.read_json()
            title = body.get("title")
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
                raise ValueError("title must contain 1 to 120 characters")
            task = {"id": str(uuid.uuid4()), "title": title.strip(), "completed": False}
            with LOCK:
                TASKS[task["id"]] = task
            self.reply(201, task)
        except (ValueError, UnicodeError) as exc:
            self.reply(400, {"error": str(exc)})

    def do_PATCH(self):
        if not self.path.startswith("/tasks/"):
            return self.reply(404, {"error": "not found"})
        try:
            body = self.read_json()
            if type(body.get("completed")) is not bool:
                raise ValueError("completed must be true or false")
            with LOCK:
                task = TASKS.get(self.path.removeprefix("/tasks/"))
                if task is None:
                    return self.reply(404, {"error": "task not found"})
                task["completed"] = body["completed"]
                result = dict(task)
            self.reply(200, result)
        except (ValueError, UnicodeError) as exc:
            self.reply(400, {"error": str(exc)})

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), Handler)
    server.daemon_threads = True
    server.serve_forever()
