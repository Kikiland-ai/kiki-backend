"""Safe comparison records: no screenshots, keys, model prose or student text."""
from datetime import datetime, timezone
import time,re

METRICS = frozenset(('provider_ms','first_byte_ms','first_finding_ms','critical_fields_ms',
    'provider_stop_ms','drawing_fields_ms','validation_ms','request_prepared_ms','drawing_tail_ms','decision_validated_ms','commit_finished_ms',
    'packet_prepared_ms','publication_ms','frame_age_at_commit_ms','input_tokens','output_tokens',
    'cached_tokens','thinking_tokens','total_tokens','request_text_characters','image_bytes',
    'provider_attempts','stream_attempts','context_db_reads','context_db_ms','routing_db_reads',
    'routing_db_ms','provider_db_operations','provider_db_ms','provider_http_attempts','provider_http_ms','provider_headers_ms','provider_first_dispatch_ms','provider_last_dispatch_ms','screen_guidance_bytes','provider_chunks','context_batches','context_events'))
STAGES = frozenset(('admitted','analysis_validated','tracker_committed','packet_prepared',
                    'published','discarded','failed','cancelled'))
REASONS = frozenset(('none','stale_context','stale_source_context','expired_frame','inactive_context',
    'foreign_frame_provenance','invalid_output','incomplete_output','provider_timeout_or_network_error',
    'analysis_cancelled','unverified_live_binding','no_matching_candidate','unresolved_required_target',
    'model_declined','revision_conflict','cancelled_context','duplicate_publication','stale_stream_context','provider_failure','cancelled'))

class GuidanceTrace:
    def __init__(self, write, *, request_id, pair_id, arm, sample_kind, model, runtime="python", configuration_id="unspecified", source_revision="uncommitted", run_id="unspecified"):
        if arm not in ('control','drawing_v1') or sample_kind not in ('offline_replay','live_provider'):
            raise ValueError('invalid_comparison_configuration')
        self.sequence=0
        self.write = write
        self.started = time.monotonic()
        self.tags = {'schema':'guidance-producer-timing/v1','request_id':request_id,'pair_id':pair_id,
                     'experiment':'analysis-owned-guidance','arm':arm,'sample_kind':sample_kind,'model':model,
                     'paint_verified':False,'run_id':run_id,'runtime':runtime,'configuration_id':configuration_id,'source_revision':source_revision}

    def emit(self, stage, *, reason='none', **metrics):
        if stage not in STAGES:
            raise ValueError('invalid_trace_stage')
        safe = {k:v for k,v in metrics.items() if k in METRICS and
                (v is None or type(v) in (int,float) and v>=0 and v<float('inf'))}
        self.sequence+=1
        record = {**self.tags,'event_sequence':self.sequence,'stage':stage,'reason':reason if reason in REASONS or re.fullmatch(r'provider_http_[1-5][0-9]{2}',reason) else 'provider_failure',
                  'server_time':datetime.now(timezone.utc).isoformat(),
                  'elapsed_ms':round((time.monotonic()-self.started)*1000,3),**safe}
        self.write(record)
        return record
