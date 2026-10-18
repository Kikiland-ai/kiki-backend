"""Transactional capture ownership, producer fencing, and fresh shared frame access."""
import hashlib
import time
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from .frames import FirestoreImages, atomic, record


class FirestoreCaptureStore:
    def __init__(self, client, collection_prefix='kiki_cloud', *, clock=time.time):
        self.client, self.clock = client, clock
        self.sessions = client.collection(collection_prefix + '_captures')
        self.images = FirestoreImages(client, collection_prefix, clock=clock)

    def _owned(self, session_id, owner, tx):
        row = record(self.sessions.document(session_id), tx)
        if not row or row['owner'] != owner:
            raise HTTPException(404, 'Session not found')
        return row

    def session(self, session_id, owner):
        row = atomic(self.client, lambda tx: self._owned(session_id, owner, tx))
        if row.get('lease_until', 0) <= self.clock() and row['status'] in ('sharing', 'paused'):
            row = {**row, 'status': 'disconnected'}
        return row

    def _event(self, tx, row, kind, data=None):
        row['event_sequence'] += 1
        event = {'event_id': f"{row['id']}:{row['event_sequence']}", 'sequence': row['event_sequence'],
                 'type': kind, 'server_time': datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(), 'data': data or {}}
        tx.set(self.sessions.document(row['id']).collection('events').document(f"{row['event_sequence']:012d}"), event)
        tx.set(self.sessions.document(row['id']), row)
        return event

    def create(self, owner):
        session_id = uuid.uuid4().hex
        row = {'id': session_id, 'owner': owner, 'created': self.clock(), 'status': 'awaiting_share',
               'frame_count': 0, 'latest_sequence': 0, 'latest': None, 'event_sequence': 0,
               'producer': None, 'fence': 0, 'lease_until': 0, 'last_admission': 0,
               'last_elapsed_ms': -1, 'last_view_revision': 1}
        atomic(self.client, lambda tx: self._event(tx, row.copy(), 'session_created'))
        return session_id

    def acquire_producer(self, session_id, owner, producer):
        def apply(tx):
            row = self._owned(session_id, owner, tx)
            if row['status'] in ('ended', 'expired') or row['lease_until'] > self.clock():
                raise HTTPException(409, 'Session ended or another producer is active')
            # Acquiring a socket never implies the user has shared again.
            self.images.discard('capture:' + session_id, transaction=tx)
            row.update(producer=producer, fence=row['fence']+1, lease_until=self.clock()+30,
                       status='awaiting_share', latest=None)
            self._event(tx, row, 'producer_attached')
            return row
        return atomic(self.client, apply)

    def _producer(self, session_id, owner, producer, fence, tx):
        row = self._owned(session_id, owner, tx)
        if row['producer'] != producer or row['fence'] != fence or row['lease_until'] <= self.clock():
            raise HTTPException(409, 'Capture producer lease lost; start a new share')
        return row

    def renew(self, session_id, owner, producer, fence):
        def apply(tx):
            row = self._producer(session_id, owner, producer, fence, tx)
            if row['status'] in ('ended', 'expired'):
                raise HTTPException(409, 'Capture ended')
            row['lease_until'] = self.clock()+30
            tx.set(self.sessions.document(session_id), row)
            return row
        return atomic(self.client, apply)

    def set_status(self, session_id, owner, status, reason, *, producer=None, fence=None):
        if status not in ('sharing', 'paused', 'ended', 'disconnected'):
            raise ValueError('Unknown capture status')
        def apply(tx):
            row = self._producer(session_id, owner, producer, fence, tx) if producer else self._owned(session_id, owner, tx)
            if row['status'] in ('ended', 'expired'):
                if status == 'ended':
                    return row
                raise HTTPException(409, 'Capture ended')
            if status != 'sharing':
                self.images.discard('capture:' + session_id, transaction=tx)
                row['latest'] = None
            row['status'] = status
            if status in ('ended', 'disconnected'):
                row.update(producer=None, lease_until=0)
            self._event(tx, row, reason, {'status': status})
            return row
        return atomic(self.client, apply)

    def release(self, session_id, owner, producer, fence):
        try:
            return self.set_status(session_id, owner, 'disconnected', 'capture_disconnected', producer=producer, fence=fence)
        except HTTPException as error:
            if error.status_code != 409:
                raise
            return None  # An obsolete socket must never disconnect its replacement.

    def frame(self, session_id, owner, producer, fence, metadata, payload):
        envelope = dict(metadata)
        def apply(tx):
            metadata = dict(envelope)
            row = self._producer(session_id, owner, producer, fence, tx)
            if row['status'] != 'sharing':
                raise HTTPException(409, 'Capture is not sharing')
            previous = row['latest']
            digest = hashlib.sha256(payload).hexdigest()
            if metadata['sequence'] == row['latest_sequence'] and previous and digest == previous['sha256']:
                if any(previous.get(k) != v for k, v in metadata.items()):
                    raise ValueError('Duplicate envelope conflicts')
                return True, row
            if metadata['sequence'] <= row['latest_sequence']:
                raise ValueError('Frame sequence must increase')
            if metadata['captured_elapsed_ms'] < row.get('last_elapsed_ms', -1) or metadata['view_revision'] < row.get('last_view_revision', 1):
                raise ValueError('Frame view/time moved backwards')
            if self.clock()-row['last_admission'] < 1.8:
                return None, row
            metadata = {**metadata, 'frame_id': f'{session_id}:1:{metadata["sequence"]}', 'sha256': digest,
                        'server_received_unix': self.clock(), 'server_received_at': datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(),
                        'skipped_sequences': max(0, metadata['sequence']-row['latest_sequence']-1)}
            self.images.put('capture:' + session_id, metadata['frame_id'], payload, transaction=tx)
            row.update(latest=metadata, latest_sequence=metadata['sequence'], frame_count=row['frame_count']+1,
                       last_admission=self.clock(), lease_until=self.clock()+30,
                       last_elapsed_ms=metadata['captured_elapsed_ms'], last_view_revision=metadata['view_revision'])
            self._event(tx, row, 'frame_received', metadata)
            return False, row
        return atomic(self.client, apply)

    def capture_access(self, session_id, owner):
        if not session_id:
            raise HTTPException(409, 'Attach a screen share first')
        def apply(tx):
            row = self._owned(session_id, owner, tx)
            active = row['status'] == 'sharing' and row['lease_until'] > self.clock()
            frame = row['latest']
            fresh = active and frame and 0 <= self.clock()-frame['server_received_unix'] <= 20
            pixels = None
            if fresh:
                try:
                    image_id, data = self.images.read('capture:' + session_id, transaction=tx)
                    if image_id == frame['frame_id']:
                        pixels = data
                except KeyError:
                    pass
            return {'status': row['status'] if active or row['status'] not in ('sharing','paused') else 'disconnected',
                    'frame': frame if fresh else None, 'pixels': pixels}
        return atomic(self.client, apply)

    def events(self, session_id, owner, after, limit):
        self.session(session_id, owner)
        query = self.sessions.document(session_id).collection('events').order_by('sequence').start_after({'sequence': after}).limit(limit)
        return [snap.to_dict() for snap in query.stream()]

    def snapshot(self, row):
        meta = row['latest']
        active = row['lease_until'] > self.clock()
        age = int((self.clock()-meta['server_received_unix'])*1000) if meta else None
        status = 'disconnected' if not active and row['status'] in ('sharing','paused') else row['status']
        return {'schema': 'screen-receiver/v1', 'session_id': row['id'], 'capture_epoch': 1,
                'capture_status': status, 'received_frame_count': row['frame_count'],
                'observation': {'mode': 'frame_receipt', 'analysis_status': 'not_enabled', 'summary': None, 'latest_frame': meta} if meta else None,
                'freshness': {'received_age_ms': age, 'stale': age is None or age > 10000 or not active},
                'evidence': {'latest_image_available': bool(meta and active and age is not None and age <= 20000),
                             'retention': 'private_latest_firestore_chunks_30s_access_ttl'}, 'last_event_sequence': row['event_sequence']}
