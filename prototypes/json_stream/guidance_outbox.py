"""Explicit SQLite producer outbox for the existing single-instance LabStore.

Not auto-installed by FastAPI. Integration supplies authenticated owner/attachment,
current tracker-derived runtime and calls cancellation on invalidations. No paint ACK.
"""
from copy import deepcopy
import json
from .guidance import build_committed, BUNDLE_VALIDATOR, require

class GuidanceOutbox:
    def __init__(self, store):
        self.store = store
        with store.lock, store.db:
            store.db.executescript('''
                CREATE TABLE IF NOT EXISTS drawing_streams (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, lab_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL, capture_epoch INTEGER NOT NULL,
                    sequence INTEGER NOT NULL, retired INTEGER NOT NULL DEFAULT 0,
                    cancelled_through_revision INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS drawing_outbox (
                    stream_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                    lab_revision INTEGER NOT NULL, message_id TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(stream_id, sequence), UNIQUE(stream_id, message_id)
                );
            ''')

    def append(self, *, owner, lab_id, stream_id, expected_revision, project_runtime,
               admission=None, model=None, cancel=None):
        """CAS publication against the actual persisted tracker revision.

        project_runtime(state) is synchronous trusted adapter code, with no I/O/await.
        It must derive current action/canonical text/frame bindings from trusted state.
        A cancellation can create/advance a stream while paused/disconnected.
        """
        db = self.store.db
        with self.store.lock:
            db.execute('BEGIN IMMEDIATE')
            try:
                state = self.store.load(lab_id, owner)
                require(state['revision'] == expected_revision, 'revision_conflict')
                r = deepcopy(project_runtime(deepcopy(state)))
                from prototypes.lab_tracking.service import LabService
                context = LabService.context(None, state)
                require(r['current_context'] == context, 'stale_context')
                row = db.execute('SELECT * FROM drawing_streams WHERE id=?', (stream_id,)).fetchone()
                if row:
                    require(row['owner']==owner and row['lab_id']==lab_id and
                            row['workspace_id']==context['workspace_id'] and row['capture_epoch']==context['capture_epoch'] and not row['retired'], 'foreign_or_retired_stream')
                    last = row['sequence']
                else:
                    last = 0
                    db.execute('INSERT INTO drawing_streams(id,owner,lab_id,workspace_id,capture_epoch,sequence) VALUES(?,?,?,?,?,0)',
                               (stream_id,owner,lab_id,context['workspace_id'],context['capture_epoch']))
                r.update(guidance_stream_id=stream_id, last_cue_sequence=last, cue_sequence=last+1, owner_id=owner)
                if cancel is None:
                    require(not row or admission['admitted_context']['lab_revision'] > row['cancelled_through_revision'], 'cancelled_context')
                    require(state['status']=='active' and state['runtime']['capture_status']=='sharing' and state['runtime']['analysis_status']=='available', 'inactive_context')
                    candidate=state['runtime'].get('candidate')
                    require(candidate is not None and candidate['admitted_context']==admission['admitted_context'], 'stale_context')
                    require(all(candidate['source_frame'][k]==admission['frame'][k] for k in ('frame_id','sha256','byte_count','view_revision')), 'foreign_frame_provenance')
                    require(all(candidate[k]==model[k] for k in ('criteria','action_findings','uncertainties')), 'foreign_analysis_result')
                    value = build_committed(admission, model, r)
                else:
                    value = {'schema':'analysis-owned-guidance/v0.1','message_type':'cancel',
                             'cancel_id':cancel['cancel_id'],'guidance_stream_id':stream_id,'cue_sequence':last+1,
                             'context':context,'reason':cancel['reason'],'issued_at':r['now']}
                    BUNDLE_VALIDATOR.validate(value)
                message_id = ('analysis:'+admission['analysis_request_id']) if cancel is None else ('cancel:'+cancel['cancel_id'])
                require(db.execute('SELECT 1 FROM drawing_outbox WHERE stream_id=? AND message_id=?',(stream_id,message_id)).fetchone() is None, 'duplicate_publication')
                db.execute('INSERT INTO drawing_outbox VALUES(?,?,?,?,?)', (stream_id,last+1,expected_revision,message_id,json.dumps(value)))
                db.execute('UPDATE drawing_streams SET sequence=?,retired=?,cancelled_through_revision=? WHERE id=?',
                           (last+1,1 if cancel and (cancel.get('retire') or cancel['reason']=='stream_retired') else 0,
                            expected_revision if cancel else (row['cancelled_through_revision'] if row else 0),stream_id))
                db.commit()
                return value
            except BaseException:
                db.rollback()
                raise
