"""Cloud bridge authentication, stable Site ownership, WebSockets and read MCP."""

import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from prototypes.screen_capture.server import create_app

SECRET = 'controlled-proxy-secret-at-least-32-characters'


class CloudAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name), proxy_secret=SECRET)
        self.client = TestClient(self.app)
        self.headers = {'x-kiki-proxy-key': SECRET, 'x-kiki-owner': 'site-owner', 'origin': 'http://testserver'}

    def tearDown(self):
        self.client.close()
        self.app.state.store.db.close()
        self.app.state.lab.store.db.close()
        self.temp.cleanup()

    def test_only_data_free_health_is_public(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        for path in ('/', '/lab-definition', '/lab-sessions', '/docs', '/openapi.json'):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get('/lab-sessions', headers={**self.headers, 'x-kiki-proxy-key': 'wrong'}).status_code, 401)
        self.assertEqual(self.client.get('/lab-sessions', headers={**self.headers, 'x-kiki-owner': ''}).status_code, 401)

    def test_authenticated_site_owner_is_stable_without_a_browser_cookie(self):
        response = self.client.post('/lab-sessions', headers=self.headers, json={'operator_trial': True, 'model_name': 'cloud-fixture'})
        self.assertEqual(response.status_code, 201)
        lab_id = response.json()['lab_session_id']
        self.assertNotIn('owner_id', response.json())
        fresh_browser = TestClient(self.app)
        try:
            self.assertEqual(fresh_browser.get(f'/lab-sessions/{lab_id}', headers=self.headers).status_code, 200)
            self.assertEqual(fresh_browser.get(f'/lab-sessions/{lab_id}', headers={**self.headers, 'x-kiki-owner': 'foreign'}).status_code, 404)
            self.assertEqual(fresh_browser.post(f'/lab-sessions/{lab_id}/context', headers={**self.headers, 'origin': 'https://foreign'}, json={'revision': 1, 'action': 'pause'}).status_code, 403)
        finally:
            fresh_browser.close()

    def test_http_secret_does_not_open_unauthenticated_websockets(self):
        sid = self.client.post('/screen-sessions', headers=self.headers).json()['session_id']
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect(f'/screen-sessions/{sid}/stream', headers={'origin': 'http://testserver'}):
                pass
        with self.client.websocket_connect(f'/screen-sessions/{sid}/stream', headers=self.headers) as ws:
            self.assertEqual(ws.receive_json()['type'], 'connected')
            ws.send_json({'type': 'capture_started'})
            self.assertEqual(ws.receive_json()['observation']['capture_status'], 'sharing')
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect(f'/screen-sessions/{sid}/stream', headers={**self.headers, 'x-kiki-owner': 'other'}):
                pass

    def test_mcp_discovery_is_data_free_and_read_tools_require_owner(self):
        discovery = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
        key_only = {'x-kiki-proxy-key': SECRET}
        response = self.client.post('/mcp', headers=key_only, json=discovery)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['result']['tools']), 4)
        rpc = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'list_lab_sessions', 'arguments': {}}}
        self.assertEqual(self.client.post('/mcp', headers=key_only, json=rpc).status_code, 401)
        self.assertEqual(self.client.post('/mcp', headers=self.headers, json=rpc).json()['result']['content'][0]['text'], '[]')

    def test_required_proxy_mode_fails_startup_without_configuration(self):
        with patch.dict('os.environ', {'KIKI_REQUIRE_PROXY': '1'}):
            with self.assertRaises(RuntimeError):
                create_app(Path(self.temp.name), proxy_secret='')
