"""Durable key rotation; shared project quotas; bounded, secret-free failover."""
import asyncio
import hashlib
import json
import math
import os
import threading
import time
import uuid
from email.utils import parsedate_to_datetime

import httpx


class AnalysisFailure(Exception):
    def __init__(self, category, retry_at_ms=None):
        super().__init__(category)
        self.retry_at_ms = retry_at_ms


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class ProviderPool:
    def __init__(self, api_key=None, transport=None, clock=time.time):
        self.clock, self.transport = clock, transport
        self.db, self.lock = None, threading.RLock()
        self.health, self.rotation, self.invalid = {}, {}, False
        raw = os.environ.get('GEMINI_API_KEYS') if api_key is None else None
        try:
            values = json.loads(raw) if raw else [{'key': api_key if api_key is not None else os.environ.get('GEMINI_API_KEY', ''), 'quota_pool': 'default'}]
            if not isinstance(values, list) or not 1 <= len(values) <= 16:
                raise ValueError()
            self.keys = []
            for value in values:
                # String arrays are convenient; conservatively share a quota pool.
                item = {'key': value, 'quota_pool': 'default'} if isinstance(value, str) else value
                if not isinstance(item, dict) or not isinstance(item.get('key'), str) or not isinstance(item.get('quota_pool', 'default'), str) or not item.get('quota_pool', 'default'):
                    raise ValueError()
                if not item['key']:
                    if raw:
                        raise ValueError()
                    continue
                key_id = digest(item['key'])
                if any(v['id'] == key_id for v in self.keys):
                    raise ValueError()  # Duplicate credentials cannot provide rotation.
                self.keys.append({'key': item['key'], 'id': key_id, 'quota_pool': item.get('quota_pool', 'default')})
            self.router_id = digest('rotation/v1:'+','.join(sorted(v['id']+':'+v['quota_pool'] for v in self.keys)))
        except (ValueError, TypeError, KeyError):
            self.keys, self.invalid = [], True

    @property
    def configured(self):
        return bool(self.keys) or self.invalid

    def bind_store(self, db, lock):
        self.db, self.lock = db, lock
        with lock, db:
            db.execute('CREATE TABLE IF NOT EXISTS provider_cooldowns(pool_id TEXT PRIMARY KEY,retry_at REAL NOT NULL,failures INTEGER NOT NULL)')
            db.execute("CREATE TABLE IF NOT EXISTS provider_rotation(router_id TEXT PRIMARY KEY,last_key TEXT,failed_keys TEXT NOT NULL DEFAULT '[]',retry_at REAL NOT NULL DEFAULT 0,lease_owner TEXT,lease_until REAL NOT NULL DEFAULT 0,last_error TEXT)")

    def get(self, pool_id):
        with self.lock:
            if self.db is None:
                return self.health.get(pool_id, (0, 0))
            row = self.db.execute('SELECT retry_at,failures FROM provider_cooldowns WHERE pool_id=?', (pool_id,)).fetchone()
            return tuple(row) if row else (0, 0)

    def save(self, pool_id, retry_at, failures=1):
        with self.lock:
            if self.db is None:
                old = self.health.get(pool_id, (0, 0))
                self.health[pool_id] = (max(old[0], retry_at), failures)
            else:
                with self.db:
                    self.db.execute('INSERT INTO provider_cooldowns VALUES(?,?,?) ON CONFLICT(pool_id) DO UPDATE SET retry_at=MAX(retry_at,excluded.retry_at),failures=excluded.failures', (pool_id, retry_at, failures))

    def acquire(self, owner):
        now = self.clock()
        with self.lock:
            if self.db is None:
                row = self.rotation.setdefault(self.router_id, {'last_key': None, 'failed_keys': '[]', 'retry_at': 0, 'lease_owner': None, 'lease_until': 0, 'last_error': None})
                if row['lease_until'] > now:
                    return None
                row.update(lease_owner=owner, lease_until=now+30)
                return dict(row)
            with self.db:
                self.db.execute('INSERT OR IGNORE INTO provider_rotation(router_id) VALUES(?)', (self.router_id,))
                row = self.db.execute('UPDATE provider_rotation SET lease_owner=?,lease_until=? WHERE router_id=? AND lease_until<=? RETURNING last_key,failed_keys,retry_at,lease_owner,lease_until,last_error', (owner, now+30, self.router_id, now)).fetchone()
                return dict(zip(('last_key','failed_keys','retry_at','lease_owner','lease_until','last_error'), row)) if row else None

    def persist(self, row, owner, release=False):
        with self.lock:
            if self.db is None:
                current = self.rotation[self.router_id]
                if current['lease_owner'] != owner:
                    raise AnalysisFailure('provider_rotation_lease_lost', int((self.clock()+5)*1000))
                current.update(row)
                if release:
                    current.update(lease_owner=None, lease_until=0)
            else:
                with self.db:
                    result = self.db.execute('UPDATE provider_rotation SET last_key=?,failed_keys=?,retry_at=?,last_error=?,lease_owner=?,lease_until=? WHERE router_id=? AND lease_owner=?', (row['last_key'], row['failed_keys'], row['retry_at'], row['last_error'], None if release else owner, 0 if release else row['lease_until'], self.router_id, owner))
                    if result.rowcount != 1:
                        raise AnalysisFailure('provider_rotation_lease_lost', int((self.clock()+5)*1000))

    def retry_after(self, value):
        if not value:
            return None
        try:
            seconds = float(value)
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError()
            return seconds
        except ValueError:
            try:
                return max(0, parsedate_to_datetime(value).timestamp() - self.clock())
            except (ValueError, TypeError, OverflowError):
                return None

    async def post(self, model, body):
        if self.invalid:
            raise AnalysisFailure('invalid_provider_configuration', int((self.clock()+900)*1000))
        if not self.keys:
            raise AnalysisFailure('provider_not_configured')
        owner = str(uuid.uuid4())
        row = self.acquire(owner)
        if row is None:
            raise AnalysisFailure('provider_rotation_busy', int((self.clock()+5)*1000))
        try:
            if row['retry_at'] > self.clock():
                raise AnalysisFailure(row['last_error'] or 'provider_cycle_cooldown', int(row['retry_at']*1000))
            if row['retry_at']:
                row.update(failed_keys='[]', retry_at=0, last_error=None)
            failed = set(json.loads(row['failed_keys']))
            deadline = asyncio.get_running_loop().time()+20
            last = row['last_error'] or 'provider_cooldown'
            async with httpx.AsyncClient(timeout=20, transport=self.transport, trust_env=True) as client:
                while True:
                    start = next((i+1 for i,v in enumerate(self.keys) if v['id'] == row['last_key']), 0)
                    ordered = self.keys[start:]+self.keys[:start]
                    eligible, future = [], []
                    for item in ordered:
                        quota_id = digest(f"{model}:{item['quota_pool']}")
                        key_id = digest('key:'+item['id'])
                        model_id = digest('model:'+model)
                        retry_at = max(self.get(quota_id)[0], self.get(key_id)[0], self.get(model_id)[0])
                        if len(self.keys) > 1 and item['id'] == row['last_key']:
                            continue
                        future.append(retry_at)
                        if item['id'] in failed or retry_at > self.clock():
                            continue
                        eligible.append((item, quota_id, key_id, model_id))
                    if not eligible:
                        row.update(retry_at=max(self.clock()+60, min(future) if future else 0), last_error=last, failed_keys=json.dumps(sorted(failed)))
                        self.persist(row, owner)
                        raise AnalysisFailure(last, int(row['retry_at']*1000))
                    remaining = deadline-asyncio.get_running_loop().time()
                    if remaining <= 0:
                        row.update(failed_keys=json.dumps(sorted(failed)), last_error=last)
                        self.persist(row, owner)
                        raise AnalysisFailure(last, int((self.clock()+5)*1000))
                    item, quota_id, key_id, model_id = eligible[0]
                    row['last_key'] = item['id']
                    self.persist(row, owner)  # reserve before any outbound request
                    response = None
                    try:
                        async with asyncio.timeout(min(remaining, 8 if len(self.keys) > 1 else 20)):
                            response = await client.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', headers={'x-goog-api-key': item['key']}, json=body)
                    except (httpx.HTTPError, TimeoutError):
                        last = 'provider_timeout_or_network_error'
                    if response is not None and response.is_success:
                        row.update(failed_keys='[]', retry_at=0, last_error=None)
                        self.persist(row, owner)
                        return response
                    if response is not None:
                        last = f'provider_http_{response.status_code}'
                    failed.add(item['id'])
                    row.update(failed_keys=json.dumps(sorted(failed)), last_error=last)
                    self.persist(row, owner)
                    status = response.status_code if response is not None else 0
                    advised = self.retry_after(response.headers.get('retry-after') if response is not None else None)
                    if status == 429:
                        self.save(quota_id, self.clock()+max(60, advised or 0))
                    elif status in (401,403):
                        self.save(key_id, self.clock()+900)
                    elif status and status < 500:
                        self.save(model_id, self.clock()+900)
                        raise AnalysisFailure(last, int((self.clock()+900)*1000))
                    elif advised is not None:
                        self.save(key_id, self.clock()+max(10, advised))
                    # 503/network: try the next distinct key immediately. Each key
                    # appears at most once until success or a full failed-cycle wait.
        finally:
            self.persist(row, owner, release=True)
