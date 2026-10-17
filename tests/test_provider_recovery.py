"""Controlled quota failures: no paid API calls or actual keys."""
import asyncio
import json
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

import httpx

from prototypes.lab_tracking.provider import AnalysisFailure, ProviderPool


class ProviderRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_after_is_durable_and_same_pool_is_not_cycled(self):
        now = [2000000000.0]
        calls = []
        def fetch(request):
            calls.append(request.headers['x-goog-api-key'])
            return httpx.Response(429, headers={'Retry-After': '120'})
        with tempfile.TemporaryDirectory() as directory:
            db = sqlite3.connect(directory+'/quota.sqlite')
            config = json.dumps([{'key':'fixture-a','quota_pool':'project-a'}, {'key':'fixture-b','quota_pool':'project-a'}])
            with patch.dict('os.environ', {'GEMINI_API_KEYS':config}):
                pool = ProviderPool(transport=httpx.MockTransport(fetch), clock=lambda: now[0])
                pool.bind_store(db, threading.RLock())
                with self.assertRaises(AnalysisFailure) as caught:
                    await pool.post('fixture-model', {})
                self.assertEqual(caught.exception.retry_at_ms, (now[0]+120)*1000)
                # Recreating the adapter cannot reset the quota cooldown.
                restarted = ProviderPool(transport=httpx.MockTransport(fetch), clock=lambda: now[0])
                restarted.bind_store(db, threading.RLock())
                with self.assertRaises(AnalysisFailure):
                    await restarted.post('fixture-model', {})
                self.assertEqual(calls, ['fixture-a'])
                now[0] += 120
                with self.assertRaises(AnalysisFailure):
                    await restarted.post('fixture-model', {})
                self.assertEqual(calls, ['fixture-a','fixture-b'])
            db.close()

    async def test_independent_pool_fallback_and_secret_free_failure(self):
        calls=[]
        def fetch(request):
            key=request.headers['x-goog-api-key'];calls.append(key)
            return httpx.Response(429, text='Do not forward private diagnostic') if key=='fixture-a' else httpx.Response(200,json={'ok':True})
        config=json.dumps([{'key':'fixture-a','quota_pool':'project-a'},{'key':'fixture-a2','quota_pool':'project-a'},{'key':'fixture-b','quota_pool':'project-b'}])
        with patch.dict('os.environ', {'GEMINI_API_KEYS':config}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch))
            result=await pool.post('fixture-model', {})
            self.assertEqual(result.json(), {'ok':True})
            self.assertEqual(calls, ['fixture-a','fixture-b'])

    async def test_network_failure_backs_off_then_recovers(self):
        now=[2000000000.0];calls=[]
        def fetch(request):
            calls.append(1)
            if len(calls)==1:
                raise httpx.ConnectError('private diagnostic')
            return httpx.Response(200,json={'ok':True})
        pool=ProviderPool(api_key='fixture', transport=httpx.MockTransport(fetch), clock=lambda:now[0])
        with self.assertRaises(AnalysisFailure) as caught:
            await pool.post('fixture-model', {})
        self.assertEqual(str(caught.exception), 'provider_timeout_or_network_error')
        self.assertEqual(caught.exception.retry_at_ms,(now[0]+60)*1000)
        with self.assertRaises(AnalysisFailure):
            await pool.post('fixture-model', {})
        self.assertEqual(len(calls),1)
        now[0]+=60
        self.assertEqual((await pool.post('fixture-model', {})).status_code,200)

    async def test_http_date_retry_after_and_invalid_configuration_are_safe(self):
        pool=ProviderPool(api_key='fixture', clock=lambda:2000000000.0)
        self.assertEqual(pool.retry_after('Wed, 18 May 2033 03:35:20 GMT'),120)
        with patch.dict('os.environ', {'GEMINI_API_KEYS':'invalid private configuration'}):
            invalid=ProviderPool()
            with self.assertRaisesRegex(AnalysisFailure,'^invalid_provider_configuration$'):
                await invalid.post('fixture',{})


class KeyRotationTests(unittest.IsolatedAsyncioTestCase):
    async def test_round_robin_is_durable_global_across_models_and_never_stores_keys(self):
        config=json.dumps(['fixture-a','fixture-b','fixture-c']);calls=[]
        def fetch(request):
            calls.append(request.headers['x-goog-api-key']);return httpx.Response(200,json={'ok':True})
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'GEMINI_API_KEYS':config}):
            db=sqlite3.connect(directory+'/rotation.sqlite');lock=threading.RLock()
            try:
                for i in range(7):
                    # A fresh adapter simulates process pickup of durable cursor.
                    pool=ProviderPool(transport=httpx.MockTransport(fetch));pool.bind_store(db,lock)
                    await pool.post('model-a' if i%2 else 'model-b',{})
                self.assertEqual(calls,['fixture-a','fixture-b','fixture-c','fixture-a','fixture-b','fixture-c','fixture-a'])
                stored=str(db.execute('SELECT * FROM provider_rotation').fetchall())
                self.assertNotIn('fixture-',stored)
            finally: db.close()

    async def test_503_tries_all_keys_then_waits_a_minute_and_recovers(self):
        now=[2000000000.0];calls=[];healthy=[False]
        def fetch(request):
            calls.append(request.headers['x-goog-api-key'])
            return httpx.Response(200,json={'ok':True}) if healthy[0] else httpx.Response(503,text='private provider body')
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b','fixture-c'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch),clock=lambda:now[0])
            with self.assertRaises(AnalysisFailure) as caught: await pool.post('model',{})
            self.assertEqual(str(caught.exception),'provider_http_503')
            self.assertEqual(caught.exception.retry_at_ms,(now[0]+60)*1000)
            self.assertEqual(calls,['fixture-a','fixture-b','fixture-c'])
            with self.assertRaises(AnalysisFailure): await pool.post('model',{})
            self.assertEqual(len(calls),3)
            now[0]+=60;healthy[0]=True
            await pool.post('model',{});await pool.post('model',{})
            self.assertEqual(calls[-2:],['fixture-a','fixture-b'])

    async def test_503_same_project_key_fallback_and_following_request_rotate(self):
        calls=[]
        def fetch(request):
            key=request.headers['x-goog-api-key'];calls.append(key)
            return httpx.Response(503) if len(calls)==1 else httpx.Response(200,json={'ok':True})
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b','fixture-c'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch))
            await pool.post('model',{});await pool.post('model',{})
        self.assertEqual(calls,['fixture-a','fixture-b','fixture-c'])

    async def test_shared_429_quota_and_long_retry_after_prevent_key_hammering(self):
        now=[2000000000.0];calls=[]
        def fetch(request):
            calls.append(request.headers['x-goog-api-key']);return httpx.Response(429,headers={'Retry-After':'180'})
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch),clock=lambda:now[0])
            with self.assertRaises(AnalysisFailure) as caught: await pool.post('model',{})
            self.assertEqual(caught.exception.retry_at_ms,(now[0]+180)*1000)
            now[0]+=60
            with self.assertRaises(AnalysisFailure): await pool.post('model',{})
            self.assertEqual(calls,['fixture-a'])

    async def test_concurrent_adapters_use_a_lease_and_do_not_reuse_the_key(self):
        started=asyncio.Event();release=asyncio.Event();calls=[]
        async def fetch(request):
            calls.append(request.headers['x-goog-api-key']);started.set();await release.wait();return httpx.Response(200,json={'ok':True})
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b'])}):
            db=sqlite3.connect(directory+'/lease.sqlite');lock=threading.RLock()
            a=ProviderPool(transport=httpx.MockTransport(fetch));b=ProviderPool(transport=httpx.MockTransport(fetch))
            a.bind_store(db,lock);b.bind_store(db,lock)
            pending=asyncio.create_task(a.post('model',{}));await started.wait()
            try:
                with self.assertRaisesRegex(AnalysisFailure,'provider_rotation_busy'): await b.post('model',{})
                release.set();await pending;await b.post('model',{})
                self.assertEqual(calls,['fixture-a','fixture-b'])
            finally: release.set();await pending;db.close()

    async def test_invalid_keys_fail_closed_and_auth_key_can_fail_over(self):
        for config in ['[]','["fixture-a","fixture-a"]','[""]','null']:
            with patch.dict('os.environ', {'GEMINI_API_KEYS':config}):
                pool=ProviderPool()
                with self.assertRaisesRegex(AnalysisFailure,'invalid_provider_configuration'): await pool.post('model',{})
        calls=[]
        def fetch(request):
            key=request.headers['x-goog-api-key'];calls.append(key)
            return httpx.Response(403) if key=='fixture-a' else httpx.Response(200,json={})
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b','fixture-c'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch));await pool.post('model',{});await pool.post('model',{})
        self.assertEqual(calls,['fixture-a','fixture-b','fixture-c'])

    async def test_unsupported_model_does_not_retry_identical_payload_on_every_key(self):
        calls=[]
        def fetch(request): calls.append(1);return httpx.Response(400)
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch))
            with self.assertRaisesRegex(AnalysisFailure,'provider_http_400'): await pool.post('model',{})
        self.assertEqual(len(calls),1)


    async def test_cancelled_request_releases_lease_and_next_request_rotates(self):
        started=asyncio.Event();calls=[]
        async def fetch(request):
            calls.append(request.headers['x-goog-api-key']);started.set()
            if len(calls)==1: await asyncio.Event().wait()
            return httpx.Response(200,json={})
        with patch.dict('os.environ', {'GEMINI_API_KEYS':json.dumps(['fixture-a','fixture-b'])}):
            pool=ProviderPool(transport=httpx.MockTransport(fetch))
            pending=asyncio.create_task(pool.post('model',{}));await started.wait();pending.cancel()
            with self.assertRaises(asyncio.CancelledError): await pending
            await pool.post('model',{})
            self.assertEqual(calls,['fixture-a','fixture-b'])
