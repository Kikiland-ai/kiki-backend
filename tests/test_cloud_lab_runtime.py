"""Capture/provider boundaries. Doubles test invariants, not hosted durability."""
import asyncio
import copy
import io
import os
import subprocess
import threading
import unittest
from types import SimpleNamespace
from uuid import uuid4

import httpx
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient

from prototypes.cloud_lab.capture import FirestoreCaptureStore
from prototypes.cloud_lab.frames import FirestoreImages
from prototypes.cloud_lab.provider_state import FirestoreProviderPool
from prototypes.cloud_lab.runtime import create_app
from prototypes.lab_tracking.provider import AnalysisFailure


class Ref:
    def __init__(self, client, path):
        self.client, self.path, self.id = client, path, path.rsplit('/', 1)[-1]
    def collection(self, name):
        return Collection(self.client, self.path+'/'+name)
    def get(self, transaction=None):
        if transaction and transaction.writing:
            raise RuntimeError('Firestore forbids reads after writes')
        value = copy.deepcopy((transaction.values if transaction else self.client.values).get(self.path))
        return SimpleNamespace(exists=value is not None, to_dict=lambda: value)
    def set(self, value):
        with self.client.lock:
            self.client.values[self.path] = copy.deepcopy(value)
    def update(self, value):
        with self.client.lock:
            self.client.values[self.path].update(copy.deepcopy(value))


class Collection:
    def __init__(self, client, path):
        self.client, self.path = client, path
    def document(self, name):
        return Ref(self.client, self.path+'/'+name)


class Tx:
    def __init__(self, values):
        self.values, self.writing = values, False
    def set(self, ref, value):
        self.writing = True
        self.values[ref.path] = copy.deepcopy(value)
    def delete(self, ref):
        self.writing = True
        self.values.pop(ref.path, None)


class Memory:
    def __init__(self):
        self.values, self.lock = {}, threading.RLock()
    def collection(self, name):
        return Collection(self, name)
    def _run_transaction(self, action):
        with self.lock:
            tx = Tx(copy.deepcopy(self.values))
            result = action(tx)
            self.values = tx.values
            return result


META = {'capture_epoch': 1, 'view_revision': 1, 'sequence': 1, 'captured_elapsed_ms': 10,
        'width': 1, 'height': 1, 'source_width': 1, 'source_height': 1, 'mime_type': 'image/jpeg', 'byte_count': 3}


class CaptureContract:
    def setup_capture(self):
        self.now = 1000.
        self.a = FirestoreCaptureStore(self.clients[0], self.prefix, clock=lambda: self.now)
        self.b = FirestoreCaptureStore(self.clients[1], self.prefix, clock=lambda: self.now)
        self.sid = self.a.create('owner')
        self.lease = self.a.acquire_producer(self.sid, 'owner', 'producer')
        self.fence = self.lease['fence']
        self.a.set_status(self.sid, 'owner', 'sharing', 'capture_started', producer='producer', fence=self.fence)

    def test_cross_client_frame_owner_expiry_stop_and_no_resurrection(self):
        self.setup_capture()
        self.a.frame(self.sid, 'owner', 'producer', self.fence, META, b'one')
        self.assertEqual(self.b.capture_access(self.sid, 'owner')['pixels'], b'one')
        with self.assertRaises(HTTPException) as error:
            self.b.capture_access(self.sid, 'foreign')
        self.assertEqual(error.exception.status_code, 404)
        self.now += 21
        self.assertIsNone(self.b.capture_access(self.sid, 'owner')['pixels'])
        self.b.set_status(self.sid, 'owner', 'ended', 'capture_stopped')
        self.assertIsNone(self.a.capture_access(self.sid, 'owner')['pixels'])
        with self.assertRaises(HTTPException):
            self.a.frame(self.sid, 'owner', 'producer', self.fence, {**META, 'sequence': 2}, b'two')

    def test_replacement_requires_fresh_share_and_old_socket_cannot_disconnect(self):
        self.setup_capture()
        with self.assertRaises(HTTPException):
            self.b.acquire_producer(self.sid, 'owner', 'replacement')
        self.a.frame(self.sid, 'owner', 'producer', self.fence, META, b'one')
        self.now += 31
        replacement = self.b.acquire_producer(self.sid, 'owner', 'replacement')
        self.assertEqual(replacement['status'], 'awaiting_share')
        self.assertIsNone(self.a.release(self.sid, 'owner', 'producer', self.fence))
        self.assertEqual(self.b.session(self.sid, 'owner')['producer'], 'replacement')
        with self.assertRaises(HTTPException):
            self.b.frame(self.sid, 'owner', 'replacement', replacement['fence'], {**META, 'sequence': 2}, b'two')
        self.b.set_status(self.sid, 'owner', 'sharing', 'capture_started', producer='replacement', fence=replacement['fence'])
        self.b.frame(self.sid, 'owner', 'replacement', replacement['fence'], {**META, 'sequence': 2}, b'two')
        self.assertEqual(self.a.capture_access(self.sid, 'owner')['pixels'], b'two')

    def test_shared_checked_frames_expire_and_replacement_deletes_old_chunks(self):
        self.setup_capture()
        first = FirestoreImages(self.clients[0], self.prefix+'_checked', clock=lambda: self.now)
        second = FirestoreImages(self.clients[1], self.prefix+'_checked', clock=lambda: self.now)
        first['lab'] = ('observation-1', b'a'*450_000)
        self.assertEqual(second['lab'], ('observation-1', b'a'*450_000))
        first['lab'] = ('observation-2', b'b')
        self.assertEqual(second['lab'], ('observation-2', b'b'))
        self.now += 31
        self.assertNotIn('lab', second)
        second.pop('lab', None)


class OfflineCaptureTests(CaptureContract, unittest.TestCase):
    def setUp(self):
        self.client = Memory()
        self.clients = [self.client, self.client]
        self.prefix = 'test_runtime'

    def test_physical_replacement_stop_leaves_no_frame_chunks(self):
        self.setup_capture()
        self.a.frame(self.sid, 'owner', 'producer', self.fence, META, b'one')
        self.now += 2
        self.b.frame(self.sid, 'owner', 'producer', self.fence, {**META, 'sequence': 2}, b'two')
        self.assertEqual(sum('_frame_chunks/' in k for k in self.client.values), 1)
        self.a.set_status(self.sid, 'owner', 'ended', 'stop')
        self.assertEqual(sum('_frame_chunks/' in k for k in self.client.values), 0)

    def test_cloud_composition_health_disables_jobs_and_private_boundary(self):
        analyzer = SimpleNamespace(configured=False)
        app = create_app(client=self.client, analyzer=analyzer, proxy_secret='x'*32)
        with TestClient(app) as client:
            self.assertEqual(client.get('/lab-sessions').status_code, 401)
            health = client.get('/health').json()
            self.assertEqual(health['lab_storage'], 'named_firestore')
            self.assertFalse(health['mixed_language']['available'])
            self.assertFalse(hasattr(app.state, 'mixed_language'))
            headers = {'x-kiki-owner': 'owner', 'x-kiki-proxy-key': 'x'*32, 'origin': 'http://testserver'}
            response = client.post('/screen-sessions', headers=headers)
            self.assertEqual(response.status_code, 201)


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = Memory()

    async def test_failed_network_attempt_is_durable_and_finite_shared_cooldown(self):
        calls = []
        async def fail(request):
            calls.append(request)
            return httpx.Response(429)
        pool = FirestoreProviderPool(self.client, api_key='fixture-key', transport=httpx.MockTransport(fail))
        with self.assertRaises(AnalysisFailure):
            await pool.post('test-model', {})
        second = FirestoreProviderPool(self.client, api_key='fixture-key', transport=httpx.MockTransport(fail))
        with self.assertRaises(AnalysisFailure):
            await second.post('test-model', {})
        self.assertEqual(len(calls), 1)
        attempts = [v for k,v in self.client.values.items() if '_provider_attempts/' in k]
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]['http_status'], 429)
        self.assertEqual(attempts[0]['status'], 'failed')
        self.assertNotIn('fixture-key', str(self.client.values))

    async def test_cancelled_stream_keeps_attempt_and_releases_shared_lease(self):
        entered = asyncio.Event()
        async def held(request):
            entered.set()
            await asyncio.Event().wait()
        pool = FirestoreProviderPool(self.client, api_key='fixture-key', transport=httpx.MockTransport(held))
        task = asyncio.create_task(pool.post('test-model', {}))
        await asyncio.wait_for(entered.wait(), 3)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        attempts = [v for k,v in self.client.values.items() if '_provider_attempts/' in k]
        self.assertEqual(attempts[0]['status'], 'cancelled')
        second = FirestoreProviderPool(self.client, api_key='fixture-key')
        self.assertIsNotNone(second.acquire('next-worker'))

    def test_shared_lease_excludes_other_worker(self):
        one = FirestoreProviderPool(self.client, api_key='fixture-key')
        two = FirestoreProviderPool(self.client, api_key='fixture-key')
        lease = one.acquire('a')
        self.assertIsNone(two.acquire('b'))
        one.persist(lease, 'a', release=True)
        self.assertIsNotNone(two.acquire('b'))


@unittest.skipUnless(os.environ.get('FIRESTORE_EMULATOR_HOST'), 'Real Firestore emulator not configured')
class EmulatorCaptureTests(CaptureContract, unittest.TestCase):
    def setUp(self):
        from google.cloud import firestore
        self.clients = [firestore.Client(project='demo-kiki-cloud-contract', database='runtime-contract') for _ in range(2)]
        self.prefix = 'contract_' + uuid4().hex


@unittest.skipUnless(os.environ.get('KIKI_CLOUD_CONTRACT') == '1', 'Authorized named database contract not enabled')
class LiveCaptureTests(CaptureContract, unittest.TestCase):
    def setUp(self):
        from google.cloud import firestore
        from google.oauth2.credentials import Credentials
        result = subprocess.run(['gcloud.cmd', 'auth', 'print-access-token', '--account=arpanvihan5@gmail.com', '--quiet'],
                                check=True, capture_output=True, text=True, timeout=30,
                                env={k:v for k,v in os.environ.items() if k != 'PYTHONPATH'})
        credentials = Credentials(result.stdout.strip())
        self.clients = [firestore.Client(project='kiki-512012', database='kiki-firedb', credentials=credentials) for _ in range(2)]
        self.prefix = 'contract_fullcloud_runtime_' + uuid4().hex

    def tearDown(self):
        # This prefix is generated here and cannot contain user collections.
        self.assertTrue(self.prefix.startswith('contract_fullcloud_runtime_'))
        for suffix in ('_captures', '_frame_manifests', '_frame_chunks', '_checked_frame_manifests',
                       '_checked_frame_chunks', '_provider_state', '_provider_attempts', '_labs', '_lab_create_receipts'):
            for snapshot in self.clients[0].collection(self.prefix+suffix).stream():
                if suffix in ('_captures', '_labs'):
                    for event in snapshot.reference.collection('events').stream():
                        event.reference.delete()
                snapshot.reference.delete()
        for client in self.clients:
            client.close()

    def test_provider_lease_and_cancel_telemetry_use_real_shared_store(self):
        async def verify():
            entered = asyncio.Event()
            async def held(request):
                entered.set()
                await asyncio.Event().wait()
            one = FirestoreProviderPool(self.clients[0], api_key='fixture-only-key', collection_prefix=self.prefix,
                                        transport=httpx.MockTransport(held))
            two = FirestoreProviderPool(self.clients[1], api_key='fixture-only-key', collection_prefix=self.prefix)
            task = asyncio.create_task(one.post('test-model', {}))
            await asyncio.wait_for(entered.wait(), 15)
            self.assertIsNone(two.acquire('other-worker'))
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            attempts = [snap.to_dict() for snap in self.clients[1].collection(self.prefix+'_provider_attempts').stream()]
            self.assertEqual(len(attempts), 1)
            self.assertEqual(attempts[0]['status'], 'cancelled')
            lease = two.acquire('replacement-worker')
            self.assertIsNotNone(lease)
            two.persist(lease, 'replacement-worker', release=True)
        asyncio.run(verify())

    def test_two_app_http_ws_private_capture_and_lab_transport(self):
        apps = [create_app(client=client, analyzer=SimpleNamespace(configured=False), proxy_secret='x'*32,
                           collection_prefix=self.prefix) for client in self.clients]
        headers = {'x-kiki-owner': 'contract-owner', 'x-kiki-proxy-key': 'x'*32, 'origin': 'http://testserver'}
        output = io.BytesIO()
        Image.new('RGB', (96, 54), (10, 20, 30)).save(output, format='JPEG')
        pixels = output.getvalue()
        with TestClient(apps[0]) as first, TestClient(apps[1]) as second:
            sid = first.post('/screen-sessions', headers=headers).json()['session_id']
            response = first.post('/lab-sessions', json={'model_name':'contract-fixture', 'operator_trial': True},
                                  headers={**headers, 'idempotency-key':'contract-create'})
            self.assertEqual(response.status_code, 201, response.text)
            lab_id = response.json()['lab_session_id']
            replay = second.post('/lab-sessions', json={'model_name':'contract-fixture', 'operator_trial': True},
                                 headers={**headers, 'idempotency-key':'contract-create'})
            self.assertEqual(replay.json()['lab_session_id'], lab_id)
            with first.websocket_connect(f'/screen-sessions/{sid}/stream', headers=headers) as ws:
                self.assertEqual(ws.receive_json()['type'], 'connected')
                ws.send_json({'type':'capture_started'})
                self.assertEqual(ws.receive_json()['observation']['capture_status'], 'sharing')
                ws.send_json({'type':'frame', **META, 'width':96, 'height':54, 'source_width':96, 'source_height':54, 'byte_count':len(pixels)})
                ws.send_bytes(pixels)
                self.assertEqual(ws.receive_json()['type'], 'ack')
                self.assertEqual(second.get(f'/screen-sessions/{sid}/frame', headers=headers).content, pixels)
                self.assertEqual(second.get(f'/screen-sessions/{sid}/frame', headers={**headers,'x-kiki-owner':'foreign'}).status_code, 404)
                stopped = second.post(f'/screen-sessions/{sid}/stop', headers=headers)
                self.assertEqual(stopped.json()['capture_status'], 'ended')
                self.assertEqual(first.get(f'/screen-sessions/{sid}/frame', headers=headers).status_code, 410)
                ws.send_json({'type':'heartbeat'})
                self.assertEqual(ws.receive_json()['type'], 'error')


if __name__ == '__main__':
    unittest.main()
