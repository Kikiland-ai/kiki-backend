"""Check a running backend the way kiki-web's API reaches it, without model calls.

Use it through an SSH forward or tunnel before a connected trial:

    KIKI_PROXY_SECRET=<same secret as the backend> python -B scripts/smoke-lab-upstream.py --origin http://127.0.0.1:8100

It sends kiki-web's headers (proxy key, `fb:` owner, Origin equal to the backend origin),
creates one lab twice with the same Idempotency-Key, opens the screen WebSocket and deletes
the lab again. The secret is read from the environment so it stays out of shell history.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

from websockets.sync.client import connect


def call(origin, method, path, headers=None, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(origin + path, data=data, method=method, headers={'content-type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, dict(response.headers), json.loads(response.read() or b'null')
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--origin', default='http://127.0.0.1:8100', help='Backend origin as kiki-web is configured to call it')
    args = parser.parse_args()
    origin = args.origin.rstrip('/')
    secret = os.environ.get('KIKI_PROXY_SECRET', '')
    if len(secret) < 32:
        sys.exit('Set KIKI_PROXY_SECRET to the backend secret (32+ characters).')
    owner = 'fb:smoke-' + uuid.uuid4().hex[:12]
    headers = {'x-kiki-proxy-key': secret, 'x-kiki-owner': owner, 'origin': origin}
    body = {'operator_trial': True, 'model_name': 'smoke_check', 'progression_mode': 'screen_guided'}
    results = []

    hints = {401: 'proxy secret or owner rejected; use the backend secret', 403: 'Origin and Host differ; do not rewrite Host in the tunnel'}

    def check(name, ok, detail=''):
        results.append(ok)
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else f' ({detail})'), flush=True)
        return ok

    def got(status):
        return f'HTTP {status}' + (f': {hints[status]}' if status in hints else '')

    status, _, health = call(origin, 'GET', '/health')
    if not check('health responds', status == 200, got(status)):
        sys.exit(1)
    check('backend is the unified FastAPI app', (health or {}).get('backend') == 'python_fastapi')
    status, _, _ = call(origin, 'POST', '/lab-sessions', {'origin': origin}, body)
    check('requests without the proxy key are refused', status == 401, f'HTTP {status}: start the backend with KIKI_REQUIRE_PROXY=1 and a secret')

    key = 'smoke-' + uuid.uuid4().hex
    status, _, first = call(origin, 'POST', '/lab-sessions', {**headers, 'Idempotency-Key': key}, body)
    if not check('fb: owner creates a lab', status == 201, got(status)):
        sys.exit(1)
    lab_id = first['lab_session_id']
    try:
        status, response_headers, again = call(origin, 'POST', '/lab-sessions', {**headers, 'Idempotency-Key': key}, body)
        replayed = {k.lower(): v for k, v in response_headers.items()}.get('idempotency-replayed')
        check('a repeated Idempotency-Key returns the same lab', status == 201 and (again or {}).get('lab_session_id') == lab_id and replayed == 'true')
        status, _, _ = call(origin, 'GET', '/lab-sessions/' + lab_id, {**headers, 'x-kiki-owner': owner + '-other'})
        check('another owner cannot read the lab', status == 404, got(status))
        status, _, screen = call(origin, 'POST', '/screen-sessions', headers)
        if check('screen session starts', status == 201, got(status)):
            socket_origin = origin.replace('https://', 'wss://').replace('http://', 'ws://')
            with connect(f"{socket_origin}/screen-sessions/{screen['session_id']}/stream", additional_headers=headers, open_timeout=15) as socket:
                check('screen WebSocket connects', json.loads(socket.recv(timeout=15)).get('type') == 'connected')
    finally:
        status, _, _ = call(origin, 'DELETE', '/lab-sessions/' + lab_id, headers)
        check('smoke lab deleted', status == 200, got(status))
    print(json.dumps({'passed': all(results), 'checks': len(results), 'origin': origin, 'model_calls': 0}))
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
