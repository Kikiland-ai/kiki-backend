"""Secret-free attempt records independent of learner progress commits."""
import time
import uuid
from contextvars import ContextVar

ATTEMPT_CONTEXT = ContextVar('cloud_provider_attempt_context', default={})


class AttemptJournal:
    def __init__(self, client, collection_prefix='kiki_cloud', *, clock=time.time):
        self.attempts = client.collection(collection_prefix + '_provider_attempts')
        self.clock = clock

    def begin(self, model, credential_id):
        ref = self.attempts.document(uuid.uuid4().hex)
        context = ATTEMPT_CONTEXT.get()
        safe = {key: context[key] for key in ('lab_session_id', 'lab_revision', 'checkpoint_id') if key in context}
        ref.set({'attempt_id': ref.id, 'model': model, 'credential_id': credential_id, 'started_unix': self.clock(),
                 'status': 'dispatch_started', 'context': safe})
        return ref

    def finish(self, ref, status, *, http_status=None, elapsed_ms=0):
        ref.update({'status': status, 'http_status': http_status, 'elapsed_ms': round(elapsed_ms),
                    'finished_unix': self.clock()})
