"""Development-only local runner; no Docker or AWS required."""
import functools
import importlib.util
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
ROOT = Path(__file__).resolve().parents[1]
def api(name, port):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'services' / name / 'app.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if name == 'summary': module.TASKS_URL = 'http://127.0.0.1:8000'
    server = ThreadingHTTPServer(('127.0.0.1', port), module.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
class Proxy(SimpleHTTPRequestHandler):
    def proxy(self):
        if self.path == '/healthz':
            self.send_response(200); self.end_headers(); self.wfile.write(b'ok'); return
        if self.path.startswith('/api/tasks'):
            target = 'http://127.0.0.1:8000' + self.path.removeprefix('/api')
        elif self.path == '/api/summary': target = 'http://127.0.0.1:8001/summary'
        else: self.send_error(404); return
        length = int(self.headers.get('Content-Length', '0'))
        if length > 4096: self.send_error(413); return
        body = self.rfile.read(length) if length else None
        req = Request(target, data=body, method=self.command, headers={'Content-Type':self.headers.get('Content-Type','application/json')})
        try:
            try: response = urlopen(req, timeout=5)
            except HTTPError as error: response = error
            with response:
                data = response.read()
                self.send_response(response.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers(); self.wfile.write(data)
        except URLError: self.send_error(502)
    def do_GET(self):
        if self.path.startswith('/api/') or self.path == '/healthz': self.proxy()
        else: super().do_GET()
    def do_POST(self): self.proxy()
    def do_PATCH(self): self.proxy()
def start():
    servers = [api('tasks',8000),api('summary',8001)]
    handler = functools.partial(Proxy, directory=str(ROOT/'services/frontend'))
    servers.append(ThreadingHTTPServer(('127.0.0.1',8080),handler))
    threading.Thread(target=servers[-1].serve_forever,daemon=True).start()
    return servers
if __name__ == '__main__':
    servers = start()
    print('Open http://localhost:8080 — Ctrl+C to stop',flush=True)
    try: threading.Event().wait()
    except KeyboardInterrupt: pass
    finally:
        for server in servers: server.shutdown(); server.server_close()
