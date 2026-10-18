"""Private transient pixels. Never place capture objects in the immutable CAM bucket.

Each replacement atomically removes the prior chunks. Access expires after 30s;
configure Firestore TTL on expires_at for physical cleanup after instance death.
Firestore TTL is asynchronous, so it is cleanup, never the authorization boundary.
"""
import hashlib
import time
import uuid
from collections.abc import MutableMapping
from datetime import datetime, timezone


def atomic(client, action):
    # Only test clients expose this hook. Production always uses SDK transactions.
    if hasattr(client, '_run_transaction'):
        return client._run_transaction(action)
    from google.cloud import firestore
    return firestore.transactional(action)(client.transaction())


def record(ref, transaction):
    snap = ref.get(transaction=transaction)
    return snap.to_dict() if snap.exists else None


class FirestoreImages(MutableMapping):
    """Latest checked frame mapping accepted by the existing domain service."""
    def __init__(self, client, collection_prefix='kiki_cloud', *, clock=time.time, ttl=30):
        if not 1 <= ttl <= 60:
            raise ValueError('Frame TTL must be between one and sixty seconds')
        self.client, self.clock, self.ttl = client, clock, ttl
        self.manifests = client.collection(collection_prefix + '_frame_manifests')
        self.chunks = client.collection(collection_prefix + '_frame_chunks')

    def ref(self, key):
        return self.manifests.document(hashlib.sha256(key.encode()).hexdigest())

    def put(self, key, observation_id, payload, *, transaction):
        if not isinstance(payload, bytes) or not 1 <= len(payload) <= 1_000_000:
            raise ValueError('Invalid frame bytes')
        ref = self.ref(key)
        old = record(ref, transaction)
        generation = uuid.uuid4().hex
        pieces = [payload[i:i+200_000] for i in range(0, len(payload), 200_000)]
        ids = [generation + '-' + str(i) for i in range(len(pieces))]
        expires = self.clock() + self.ttl
        for chunk_id, piece in zip(ids, pieces):
            transaction.set(self.chunks.document(chunk_id), {'bytes': piece, 'expires_at': datetime.fromtimestamp(expires, timezone.utc)})
        transaction.set(ref, {'id': observation_id, 'chunks': ids, 'sha256': hashlib.sha256(payload).hexdigest(),
                              'expires_unix': expires, 'expires_at': datetime.fromtimestamp(expires, timezone.utc)})
        for chunk_id in (old or {}).get('chunks', []):
            transaction.delete(self.chunks.document(chunk_id))

    def read(self, key, *, transaction):
        manifest = record(self.ref(key), transaction)
        if not manifest or manifest['expires_unix'] <= self.clock():
            raise KeyError(key)
        pieces = [record(self.chunks.document(i), transaction) for i in manifest['chunks']]
        if any(not piece for piece in pieces):
            raise KeyError(key)
        payload = b''.join(piece['bytes'] for piece in pieces)
        if hashlib.sha256(payload).hexdigest() != manifest['sha256']:
            raise KeyError(key)
        return manifest['id'], payload

    def discard(self, key, *, transaction):
        ref = self.ref(key)
        manifest = record(ref, transaction)
        for chunk_id in (manifest or {}).get('chunks', []):
            transaction.delete(self.chunks.document(chunk_id))
        transaction.delete(ref)

    def __getitem__(self, key):
        return atomic(self.client, lambda tx: self.read(key, transaction=tx))

    def __setitem__(self, key, value):
        observation_id, payload = value
        atomic(self.client, lambda tx: self.put(key, observation_id, payload, transaction=tx))

    def __delitem__(self, key):
        atomic(self.client, lambda tx: self.discard(key, transaction=tx))

    def discard_if(self, key, observation_id):
        """A delayed invalidation must not delete a newer checked observation."""
        def apply(tx):
            ref = self.ref(key)
            manifest = record(ref, tx)
            if not manifest or manifest['id'] != observation_id:
                return False
            for chunk_id in manifest['chunks']:
                tx.delete(self.chunks.document(chunk_id))
            tx.delete(ref)
            return True
        return atomic(self.client, apply)

    def pop(self, key, default=None):
        # Domain invalidation needs deletion only; never load pixels to discard them.
        self.__delitem__(key)
        return default

    def __iter__(self):
        raise TypeError('Frame enumeration is deliberately unavailable')

    def __len__(self):
        raise TypeError('Frame enumeration is deliberately unavailable')
