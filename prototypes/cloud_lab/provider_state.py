"""Cloud-only finite provider failover; every dispatch has independent telemetry."""
import asyncio
import json
import time
import uuid

import httpx
from prototypes.lab_tracking.provider import ProviderPool, AnalysisFailure, digest
from .frames import atomic, record
from .telemetry import AttemptJournal


class FirestoreProviderPool(ProviderPool):
    def __init__(self, client, *args, collection_prefix='kiki_cloud', **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.states = client.collection(collection_prefix + '_provider_state')
        self.journal = AttemptJournal(client, collection_prefix, clock=self.clock)
        self.io_mode = 'firestore_transactions'

    def bind_store(self, *args):
        raise RuntimeError('A cloud provider cannot bind a SQLite store')

    def get(self, pool_id):
        row = atomic(self.client, lambda tx: record(self.states.document('cooldown-' + pool_id), tx))
        return ((row or {}).get('retry_at', 0), (row or {}).get('failures', 0))

    def save(self, pool_id, retry_at, failures=1):
        def apply(tx):
            ref = self.states.document('cooldown-' + pool_id)
            old = record(ref, tx) or {}
            tx.set(ref, {'retry_at': max(old.get('retry_at', 0), retry_at), 'failures': failures})
        atomic(self.client, apply)

    def acquire(self, owner):
        def apply(tx):
            ref = self.states.document('rotation-' + self.router_id)
            row = record(ref, tx) or {'last_key': None, 'failed_keys': '[]', 'retry_at': 0, 'lease_owner': None, 'lease_until': 0, 'last_error': None}
            if row['lease_until'] > self.clock():
                return None
            row.update(lease_owner=owner, lease_until=self.clock()+30)
            tx.set(ref, row)
            return row
        return atomic(self.client, apply)

    def persist(self, row, owner, release=False):
        def apply(tx):
            ref = self.states.document('rotation-' + self.router_id)
            old = record(ref, tx)
            if not old or old['lease_owner'] != owner or old['lease_until'] <= self.clock():
                raise AnalysisFailure('provider_rotation_lease_lost')
            value = {**row}
            if release:
                value.update(lease_owner=None, lease_until=0)
            tx.set(ref, value)
        atomic(self.client, apply)

    async def post(self, model, body):
        return await self._execute(model, body)

    async def stream(self, model, body, consume, reset, metrics_sink=None):
        return await self._execute(model, body, consume=consume, reset=reset, metrics_sink=metrics_sink)

    async def _execute(self, model, body, *, consume=None, reset=None, metrics_sink=None):
        if self.invalid:
            raise AnalysisFailure('invalid_provider_configuration')
        if not self.keys:
            raise AnalysisFailure('provider_not_configured')
        owner = uuid.uuid4().hex
        row = self.acquire(owner)
        if row is None:
            raise AnalysisFailure('provider_rotation_busy', int((self.clock()+5)*1000))
        metrics = {'provider_io_mode': self.io_mode, 'provider_http_attempts': 0, 'provider_http_ms': 0}
        try:
            if row['retry_at'] > self.clock():
                raise AnalysisFailure(row['last_error'] or 'provider_cycle_cooldown', int(row['retry_at']*1000))
            failed = set() if row['retry_at'] else set(json.loads(row['failed_keys']))
            row.update(retry_at=0, last_error=None)
            deadline = asyncio.get_running_loop().time()+20
            start = next((i+1 for i,item in enumerate(self.keys) if item['id'] == row['last_key']), 0)
            ordered = self.keys[start:] + self.keys[:start]
            last, future = 'provider_cooldown', []
            async with httpx.AsyncClient(timeout=20, transport=self.transport, trust_env=True) as client:
                for item in ordered:  # At most one actual HTTP attempt per distinct key.
                    quota_id, key_id, model_id = digest(f"{model}:{item['quota_pool']}"), digest('key:'+item['id']), digest('model:'+model)
                    retry_at = max(self.get(value)[0] for value in (quota_id, key_id, model_id))
                    future.append(retry_at)
                    if item['id'] in failed or retry_at > self.clock():
                        continue
                    remaining = deadline-asyncio.get_running_loop().time()
                    if remaining <= 0:
                        break
                    row.update(last_key=item['id'])
                    self.persist(row, owner)
                    if reset is not None:
                        await reset()
                    # Must commit before HTTP begins. Crash here leaves an explicitly
                    # uncertain dispatch_started record, never a fabricated completion.
                    attempt = self.journal.begin(model, item['id'])
                    began = time.monotonic()
                    status, advised, outcome = None, None, 'failed'
                    metrics['provider_http_attempts'] += 1
                    try:
                        async with asyncio.timeout(min(remaining, 8 if len(self.keys) > 1 else 20)):
                            if consume is not None:
                                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse'
                                async with client.stream('POST', url, headers={'x-goog-api-key': item['key']}, json=body) as response:
                                    status = response.status_code
                                    advised = self.retry_after(response.headers.get('retry-after'))
                                    if response.is_success:
                                        result = await consume(response)
                                        outcome = 'succeeded'
                                        row.update(failed_keys='[]', retry_at=0, last_error=None)
                                        return result
                            else:
                                response = await client.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent', headers={'x-goog-api-key': item['key']}, json=body)
                                status = response.status_code
                                advised = self.retry_after(response.headers.get('retry-after'))
                                if response.is_success:
                                    outcome = 'succeeded'
                                    row.update(failed_keys='[]', retry_at=0, last_error=None)
                                    return response
                    except (httpx.HTTPError, TimeoutError):
                        outcome = 'timeout_or_network_error'
                    except asyncio.CancelledError:
                        outcome = 'cancelled'
                        raise
                    finally:
                        elapsed = (time.monotonic()-began)*1000
                        metrics['provider_http_ms'] += elapsed
                        self.journal.finish(attempt, outcome, http_status=status, elapsed_ms=elapsed)
                    last = f'provider_http_{status}' if status else 'provider_timeout_or_network_error'
                    failed.add(item['id'])
                    row.update(failed_keys=json.dumps(sorted(failed)), last_error=last)
                    self.persist(row, owner)
                    if status == 429:
                        self.save(quota_id, self.clock()+max(60, advised or 0))
                    elif status in (401,403):
                        self.save(key_id, self.clock()+900)
                    elif status and status < 500:
                        self.save(model_id, self.clock()+900)
                        raise AnalysisFailure(last, int((self.clock()+900)*1000))
                    elif advised is not None:
                        self.save(key_id, self.clock()+max(10, advised))
            row.update(retry_at=max(self.clock()+60, min(future) if future else 0), last_error=last,
                       failed_keys=json.dumps(sorted(failed)))
            raise AnalysisFailure(last, int(row['retry_at']*1000))
        except BaseException as error:
            error.provider_metrics = dict(metrics)
            raise
        finally:
            try:
                self.persist(row, owner, release=True)
            finally:
                if metrics_sink is not None:
                    metrics_sink(dict(metrics))


FirestoreStreamingProviderPool = FirestoreProviderPool
