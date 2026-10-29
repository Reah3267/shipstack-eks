import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError
base = sys.argv[1].rstrip('/')
for attempt in range(30):
    try:
        with urlopen(base + '/healthz', timeout=2) as r:
            assert r.status == 200
        break
    except (URLError, OSError):
        if attempt == 29:
            raise
        time.sleep(1)
def call(path, method='GET', data=None):
    payload = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(base + path, data=payload, method=method, headers={'Content-Type':'application/json'}), timeout=5) as r:
        return json.load(r)
task = call('/api/tasks', 'POST', {'title':'CI deployment smoke test'})
assert task['completed'] is False
result = call('/api/tasks/' + task['id'], 'PATCH', {'completed':True})
assert result['completed'] is True
assert any(t['id'] == task['id'] for t in call('/api/tasks'))
summary = call('/api/summary')
assert summary['total'] >= 1 and summary['completed'] >= 1
assert summary['pending'] + summary['completed'] == summary['total']
print('PASS: frontend proxy, task creation, update, listing and service-to-service summary')
