import importlib.util
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'services' / name / 'app.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
class Services(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = load('tasks')
        cls.summary = load('summary')
        cls.servers = []
        for module in (cls.tasks, cls.summary):
            server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            cls.servers.append(server)
        cls.tasks_url = f'http://127.0.0.1:{cls.servers[0].server_port}'
        cls.summary_url = f'http://127.0.0.1:{cls.servers[1].server_port}'
        cls.summary.TASKS_URL = cls.tasks_url
    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            server.shutdown()
            server.server_close()
    def setUp(self):
        self.tasks.TASKS.clear()
        self.summary.TASKS_URL = self.tasks_url
    def call(self, base, path, method='GET', data=None):
        payload = json.dumps(data).encode() if data is not None else None
        req = Request(base + path, data=payload, method=method, headers={'Content-Type':'application/json'})
        try:
            with urlopen(req, timeout=5) as r: return r.status, json.load(r)
        except HTTPError as e: return e.code, json.load(e)
    def test_create_list_complete_summary(self):
        code, task = self.call(self.tasks_url, '/tasks', 'POST', {'title':' Deploy EKS '})
        self.assertEqual(code, 201)
        self.assertEqual(task['title'], 'Deploy EKS')
        self.assertEqual(self.call(self.tasks_url, '/tasks')[1], [task])
        code, changed = self.call(self.tasks_url, '/tasks/' + task['id'], 'PATCH', {'completed':True})
        self.assertEqual(code, 200)
        self.assertTrue(changed['completed'])
        self.assertEqual(self.call(self.summary_url, '/summary'), (200, {'total':1,'completed':1,'pending':0}))
    def test_empty_summary(self):
        self.assertEqual(self.call(self.summary_url, '/summary')[1], {'total':0,'completed':0,'pending':0})
    def test_invalid_titles(self):
        for title in ['', '  ', 7, None, 'x'*121]:
            with self.subTest(title=title):
                self.assertEqual(self.call(self.tasks_url, '/tasks', 'POST', {'title':title})[0], 400)
    def test_patch_validation_and_missing_id(self):
        self.assertEqual(self.call(self.tasks_url, '/tasks/missing', 'PATCH', {'completed':'yes'})[0], 400)
        self.assertEqual(self.call(self.tasks_url, '/tasks/missing', 'PATCH', {'completed':True})[0], 404)
    def test_malformed_json(self):
        req = Request(self.tasks_url + '/tasks', data=b'{broken', headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as error: urlopen(req, timeout=3)
        self.assertEqual(error.exception.code, 400)
    def test_non_object_and_large_body(self):
        for body in [[], 'not an object', {'title':'x'*5000}]:
            self.assertEqual(self.call(self.tasks_url, '/tasks', 'POST', body)[0], 400)
    def test_upstream_failure_is_503(self):
        self.summary.TASKS_URL = 'http://127.0.0.1:1'
        self.assertEqual(self.call(self.summary_url, '/summary')[0], 503)
    def test_health_and_not_found(self):
        for base in [self.tasks_url, self.summary_url]:
            self.assertEqual(self.call(base, '/healthz')[0], 200)
            self.assertEqual(self.call(base, '/missing')[0], 404)
if __name__ == '__main__': unittest.main()
