"""Domain rules: frozen observations, reviewed criteria, visits and bounded telemetry."""

import asyncio
import copy
import hashlib
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .analysis import AnalysisFailure, GeminiAnalyzer, validate_result
from .definition import CHECKPOINTS, DEFINITION, DEFINITION_HASH, ORDER, expected_condition
from .store import LabStore
from .guided import POLICY, guidance, next_instruction, observe, supported, procedure_guidance, update_procedure_history

FRAME_AGE_SECONDS = 20
CHECK_INTERVAL_SECONDS = 3


def new_id():
    return str(uuid4())


class LabService:
    def __init__(self, directory, capture, analyzer=None, clock=time.time):
        self.store = LabStore(directory)
        self.capture = capture
        self.analyzer = analyzer if analyzer is not None else GeminiAnalyzer()
        self.clock = clock
        if hasattr(self.analyzer, "provider"):
            self.analyzer.provider.bind_store(self.store.db, self.store.lock)
        self.images = {}  # latest checked JPEG only; never written to the SQLite journal
        self.provider_slots = asyncio.Semaphore(4)
        for state in self.store.all():
            if state["status"] != "completed":
                # The interval since the last durable write is unobserved after a crash.
                # Conservatively classify it as a gap, never continuous tracking.
                state["runtime"]["capture_status"] = "disconnected"
                self.account_time(state)
                self.invalidate(state, "server_restarted")
                self.save(state, "server_restarted")

    def timestamp(self, at=None):
        return datetime.fromtimestamp(self.clock() if at is None else at, timezone.utc).isoformat()

    @staticmethod
    def expect(state, revision):
        if revision != state["revision"]:
            raise HTTPException(409, "Lab revision changed; refresh before editing")

    @staticmethod
    def current_step(state):
        return state["steps"].get(state["queue"]["current_checkpoint_id"])

    def context(self, state):
        return {"lab_session_id": state["lab_session_id"], "experiment_id": state["experiment_id"],
                "checkpoint_id": state["queue"]["current_checkpoint_id"], "visit_id": state["current_visit_id"],
                "lab_revision": state["revision"], "workspace_id": state["workspace"]["id"],
                **{k: state["workspace"][k] for k in ("capture_epoch", "view_revision", "parameter_revision", "condition")}}

    def account_time(self, state):
        now = self.clock()
        elapsed = max(0, now - state["runtime"]["last_accounted"])
        step = self.current_step(state)
        if step and state["status"] != "completed":
            timing = step["timing"]
            timing["wall_ms"] += int(elapsed * 1000)
            field = "paused_ms" if state["status"] == "paused" else "tracking_active_ms" if state["runtime"]["capture_status"] == "sharing" else "disconnected_ms"
            timing[field] += int(elapsed * 1000)
            candidate = state["runtime"]["candidate"]
            if field == "tracking_active_ms" and candidate:
                start = max(state["runtime"]["last_accounted"], candidate["source_frame"]["server_received_unix"])
                end = min(now, candidate["source_frame"]["server_received_unix"] + FRAME_AGE_SECONDS)
                timing["valid_observation_ms"] += int(max(0, end - start) * 1000)
        state["runtime"]["last_accounted"] = now

    def event(self, state, kind, payload=None, actor="system", origin=None):
        return {"schema": "lab-event/v1", "event_id": new_id(), "event_sequence": state["revision"],
                "event_type": kind, "received_at": self.timestamp(), "timestamp_authority": "observer_server_utc",
                "actor_type": actor, "context": origin or self.context(state), "payload": payload or {}}

    def save(self, state, kind, payload=None, actor="system", origin=None):
        self.account_time(state)
        expected = state["revision"]
        state["revision"] += 1
        self.store.save(state, expected, self.event(state, kind, payload, actor, origin))
        return self.project(state)

    def start(self, owner, body):
        if not body.model_name.strip():
            raise HTTPException(422, "Enter your saved model name")
        steps = {}
        for i, cp in enumerate(DEFINITION["checkpoints"]):
            visit = new_id() if i == 0 else None
            steps[cp["id"]] = {"checkpoint_id": cp["id"], "status": "in_progress" if i == 0 else "upcoming",
                "current_visit_id": visit, "visits": [visit] if visit else [], "attempt_count": 1 if visit else 0,
                "criteria": [{"criterion_id": c["id"], "state": "unknown", "evidence_ids": [], "parameter_revision": None} for c in cp["completion_criteria"]],
                "timing": {"wall_ms": 0, "tracking_active_ms": 0, "paused_ms": 0, "disconnected_ms": 0, "valid_observation_ms": 0},
                "telemetry": {"analysis_attempts": 0, "analysis_failures": 0, "answer_count": 0, "help_request_count": 0}}
        concept_ids = sorted({cid for cp in CHECKPOINTS.values() for cid in cp["concept_ids"]})
        state = {"schema": "lab-python/v1", "lab_session_id": new_id(), "owner_id": owner, "experiment_id": "PR-AM-DSB",
            "definition": {"definition_id": DEFINITION["id"], "definition_sha256": DEFINITION_HASH, "source": DEFINITION["source"]},
            "revision": 1, "status": "active", "synthetic": False, "mode": "operator_trial", "progression_mode": body.progression_mode,
            "auto_tracking": {},
            "readiness": {"required_concept_gate": "unknown", "operator_trial_override": True},
            "learner_state": {"concepts": [{"concept_id": cid, "understanding": "unknown", "assessment_run_ids": []} for cid in concept_ids]},
            "workspace": {"id": new_id(), "model_name": body.model_name.strip(), "software": "simulink_online", "confirmed": False,
                          "capture_session_id": None, "capture_epoch": 0, "view_revision": 1, "parameter_revision": 0,
                          "condition": "baseline", "geometry_detection": "dimensions_and_manual_reports_only"},
            "queue": {"current_checkpoint_id": ORDER[0], "upcoming_checkpoint_ids": ORDER[1:], "done_checkpoint_ids": []},
            "current_visit_id": steps[ORDER[0]]["current_visit_id"], "steps": steps, "evidence": [], "responses": [],
            "observation": None,
            "runtime": {"capture_status": "disconnected", "last_accounted": self.clock(), "last_analysis_started": None,
                        "analysis_attempts": 0, "analysis_status": "not_checked", "analysis_token": None, "candidate": None}}
        self.store.create(state, self.event(state, "session_started", {"model_name": state["workspace"]["model_name"]}, "student"))
        return self.project(state)

    def load(self, lab_id, owner):
        return self.store.load(lab_id, owner)

    def project(self, state):
        value = copy.deepcopy(state)
        self.account_time(value)
        cp = CHECKPOINTS.get(value["queue"]["current_checkpoint_id"])
        candidate = value["runtime"]["candidate"]
        age = max(0, int((self.clock() - candidate["source_frame"]["server_received_unix"]) * 1000)) if candidate else None
        if value["observation"]:
            value["observation"]["age_ms"] = age
            value["observation"]["status"] = "available" if age is not None and age <= 20000 else "stale"
        value["guidance"] = {"state": "ended" if value["status"] == "completed" else "paused" if value["status"] == "paused"
            else "disconnected" if value["runtime"]["capture_status"] != "sharing" else "current_step" if age is not None and age <= 20000 else "waiting_for_observation",
            "instruction": cp["instruction"]["en"] if cp else "Experiment complete; export your journal.",
            "reason": cp["why"]["en"] if cp else None, "expected": cp["expected"] if cp else None,
            "next_instruction": CHECKPOINTS[value["queue"]["upcoming_checkpoint_ids"][0]]["instruction"]["en"] if value["queue"]["upcoming_checkpoint_ids"] else None,
            "context": self.context(value), "pointer_active": False}
        if value.get('progression_mode') == 'screen_guided' and cp:
            procedure = procedure_guidance(cp['id'], self.current_step(value)['criteria'], value.get('procedure_tracking'), self.clock()*1000, value.get('procedure_history'))
            value['guidance'].update(procedure)
            value['guidance']['instruction'] = guidance(cp['id'], self.current_step(value)['criteria'], value.get('procedure_tracking'), self.clock()*1000, value.get('procedure_history'))
            done = value['queue']['done_checkpoint_ids']
            value['guidance']['already_tracked'] = POLICY['completed_summaries'].get(done[-1]) if done else None
            value['guidance']['already_tracked_basis'] = 'earlier_checkpoint_record_not_new_screen_claim'
            value['guidance']['next_instruction'] = next_instruction(self.current_step(value)['criteria'], value['queue']['upcoming_checkpoint_ids'], cp['id'], value.get('procedure_tracking'), self.clock()*1000, value.get('procedure_history'))
            value['guidance']['progress_basis'] = 'screen_inferred_or_student_report_not_assessment'
        value["runtime"]["provider_configured"] = self.analyzer.configured
        value["runtime"]["check_budget"] = None
        value["runtime"]["retry_after_ms"] = max(0, value["runtime"].get("retry_at_ms", 0) - int(self.clock()*1000))
        value["runtime"]["minimum_interval_seconds"] = CHECK_INTERVAL_SECONDS
        value["runtime"].pop("analysis_token", None)
        # The local owner cookie is a bearer capability, not a public learner ID.
        value.pop("owner_id", None)
        return value

    def invalidate(self, state, reason):
        state["runtime"]["candidate"] = None
        state["observation"] = None
        state["runtime"]["analysis_token"] = None
        state["runtime"]["analysis_status"] = "invalidated"
        state["runtime"]["invalidation_reason"] = reason
        self.images.pop(state["lab_session_id"], None)
        if reason != 'view_changed':
            state['auto_tracking'] = {}
            state['procedure_tracking'] = {}
            if reason not in ('pause','resume','server_restarted') and not reason.startswith('capture_'):
                state['procedure_history'] = {}
            for c in (self.current_step(state) or {}).get('criteria', []):
                if c.get('completion_basis') == 'screen_inferred':
                    c.update(state='unknown', evidence_ids=[], completion_basis=None)

    def finish_guided(self, state):
        step = self.current_step(state)
        if not step or not all(c['state'] == 'satisfied' for c in step['criteria']):
            return False
        if state['status'] != 'active' or state['runtime']['capture_status'] != 'sharing':
            return False
        for c in step['criteria']:
            if c.get('completion_basis') == 'screen_inferred':
                reading = state.get('auto_tracking', {}).get(c['criterion_id'])
                if not reading or self.clock()*1000-reading['last_seen_ms'] > POLICY['support_age_ms']:
                    return False
        cp_id = step['checkpoint_id']
        if state['workspace']['condition'] != expected_condition(cp_id):
            return False
        self.account_time(state)
        step['status'] = 'done'
        step['completion_basis'] = 'screen_inferred_or_student_report'
        step['assessment_status'] = 'unassessed'
        state['queue']['done_checkpoint_ids'].append(cp_id)
        state['queue']['current_checkpoint_id'] = state['queue']['upcoming_checkpoint_ids'].pop(0) if state['queue']['upcoming_checkpoint_ids'] else None
        next_step = self.current_step(state)
        if next_step:
            next_step.update(status='in_progress', current_visit_id=new_id())
            next_step['visits'].append(next_step['current_visit_id'])
            next_step['attempt_count'] += 1
            state['current_visit_id'] = next_step['current_visit_id']
            condition = expected_condition(next_step['checkpoint_id'])
            if condition != state['workspace']['condition']:
                state['workspace']['condition'] = condition
                state['workspace']['parameter_revision'] += 1
                state['workspace']['condition_basis'] = 'checkpoint_intent_not_verified_model_state'
        else:
            state['current_visit_id'] = None
            state['status'] = 'completed'
        if cp_id == ORDER[0]:
            state['workspace']['confirmed'] = True
        self.invalidate(state, 'checkpoint_changed')
        return True

    def apply_guided(self, state, candidate):
        if state.get('progression_mode') != 'screen_guided':
            return False
        cp_id = state['queue']['current_checkpoint_id']
        scope = {k: candidate['admitted_context'][k] for k in ('visit_id', 'workspace_id', 'capture_epoch', 'parameter_revision', 'condition')}
        state['auto_tracking'] = observe(state.get('auto_tracking', {}), candidate['criteria'], candidate['source_frame']['frame_id'], self.clock()*1000, scope)
        action_readings = [{'criterion_id': a['action_id'], 'status': a['status'], 'evidence': a['evidence']} for a in candidate.get('action_findings', [])]
        state['procedure_tracking'] = observe(state.get('procedure_tracking', {}), action_readings, candidate['source_frame']['frame_id'], self.clock()*1000, scope)
        state['procedure_history'] = update_procedure_history(state.get('procedure_history'), state['procedure_tracking'], action_readings, scope)
        # Aggregate the two separately inspected phase fields inside one visit/condition.
        for criterion_id, parts in POLICY['criterion_parts'].items():
            if criterion_id.startswith(cp_id+':') and not any(f['criterion_id']==criterion_id and f['status']=='mismatch' for f in candidate['criteria']) and all(state['procedure_tracking'].get(a, {}).get('count', 0) >= POLICY['minimum_matches'] for a in parts):
                readings = [state['procedure_tracking'][a] for a in parts]
                state['auto_tracking'][criterion_id] = {'scope': scope, 'count': POLICY['minimum_matches'], 'last_seen_ms': min(r['last_seen_ms'] for r in readings), 'last_frame_id': candidate['source_frame']['frame_id'], 'frame_ids': list(dict.fromkeys(fid for r in readings for fid in r['frame_ids'])), 'derived_action_ids': parts}
            elif state['auto_tracking'].get(criterion_id, {}).get('derived_action_ids'):
                state['auto_tracking'].pop(criterion_id, None)
        observed = supported(state['auto_tracking'], cp_id)
        for c in self.current_step(state)['criteria']:
            cid = c['criterion_id']
            if cid in observed and c['state'] != 'satisfied':
                evidence = {'evidence_id': new_id(), 'origin': 'vision_model', 'review_status': 'unreviewed',
                            'context': candidate['admitted_context'], 'frame_ids': state['auto_tracking'][cid]['frame_ids'],
                            'observation_id': candidate['observation_id'], 'criterion_ids': [cid], 'synthetic': False}
                state['evidence'].append(evidence)
                c.update(state='satisfied', completion_basis='screen_inferred', parameter_revision=state['workspace']['parameter_revision'], evidence_ids=[evidence['evidence_id']])
            elif cid not in observed and c.get('completion_basis') == 'screen_inferred':
                c.update(state='unknown', evidence_ids=[], completion_basis=None)
        return self.finish_guided(state)

    def attach(self, lab_id, owner, body):
        state = self.load(lab_id, owner)
        self.expect(state, body.revision)
        if state["status"] == "completed":
            raise HTTPException(409, "Start another run for a completed experiment")
        captured = self.capture(body.capture_session_id, owner)
        if captured["status"] != "sharing":
            raise HTTPException(409, "Start screen sharing first")
        self.account_time(state)
        self.invalidate(state, "capture_attached")
        state["workspace"]["capture_session_id"] = body.capture_session_id
        state["workspace"]["capture_epoch"] += 1
        state["runtime"]["capture_status"] = "sharing"
        return self.save(state, "capture_attached", actor="student")

    def capture_changed(self, capture_id, status, view_revision=None):
        for state in self.store.all():
            if state["workspace"]["capture_session_id"] != capture_id or state["status"] == "completed":
                continue
            changed_view = view_revision is not None and view_revision > state["workspace"]["view_revision"]
            if state["runtime"]["capture_status"] == status and not changed_view:
                continue
            self.account_time(state)
            state["runtime"]["capture_status"] = status
            if changed_view:
                state["workspace"]["view_revision"] = view_revision
            self.invalidate(state, "view_changed" if changed_view else f"capture_{status}")
            self.save(state, "view_changed" if changed_view else f"capture_{status}")

    def change(self, lab_id, owner, body):
        state = self.load(lab_id, owner)
        self.expect(state, body.revision)
        if state["status"] == "completed":
            raise HTTPException(409, "This lab is completed; export or start another run")
        cp_id = state["queue"]["current_checkpoint_id"]
        origin = self.context(state)
        step = self.current_step(state)
        self.account_time(state)
        if body.action == 'enable_guided':
            state['progression_mode'] = 'screen_guided'
            state['auto_tracking'] = {}
            state['procedure_tracking'] = {}
            state['workspace']['condition'] = expected_condition(cp_id)
            state['workspace']['condition_basis'] = 'checkpoint_intent_not_verified_model_state'
        elif body.action in ("pause", "resume"):
            state["status"] = "paused" if body.action == "pause" else "active"
        elif body.action == "view_changed":
            if body.view_revision is None or body.view_revision <= state["workspace"]["view_revision"]:
                raise HTTPException(422, "View revision must increase")
            state["workspace"]["view_revision"] = body.view_revision
        elif body.action in ("parameters_changed", "condition"):
            if body.action == "condition":
                if body.condition != expected_condition(cp_id):
                    raise HTTPException(409, "Condition belongs to another checkpoint")
                state["workspace"]["condition"] = body.condition
            state["workspace"]["parameter_revision"] += 1
            for c in step["criteria"]:
                c.update(state="unknown", evidence_ids=[], parameter_revision=None)
        elif body.action == "revisit":
            if body.checkpoint_id not in ORDER or ORDER.index(body.checkpoint_id) > ORDER.index(cp_id):
                raise HTTPException(409, "Revisit only this checkpoint or an earlier checkpoint")
            index = ORDER.index(body.checkpoint_id)
            for cid in ORDER[index:]:
                target = state["steps"][cid]
                target["status"] = "in_progress" if cid == body.checkpoint_id else "upcoming"
                target["current_visit_id"] = new_id() if cid == body.checkpoint_id else None
                if target["current_visit_id"]:
                    target["visits"].append(target["current_visit_id"])
                    target["attempt_count"] += 1
                for c in target["criteria"]:
                    c.update(state="unknown", evidence_ids=[], parameter_revision=None)
            state["queue"] = {"current_checkpoint_id": body.checkpoint_id, "done_checkpoint_ids": ORDER[:index], "upcoming_checkpoint_ids": ORDER[index+1:]}
            state["current_visit_id"] = state["steps"][body.checkpoint_id]["current_visit_id"]
            state["workspace"]["parameter_revision"] += 1
            # The physical model has not changed; preserve its declared condition.
        self.invalidate(state, body.action)
        return self.save(state, body.action, body.model_dump(exclude={"revision"}), "student", origin)

    def respond(self, lab_id, owner, body):
        state = self.load(lab_id, owner)
        self.expect(state, body.revision)
        if not body.text.strip() or not self.current_step(state):
            raise HTTPException(422, "Enter a response during a checkpoint")
        record = {"id": new_id(), "kind": body.kind, "text": body.text.strip(), "self_confidence": body.self_confidence,
                  "checkpoint_id": state["queue"]["current_checkpoint_id"], "visit_id": state["current_visit_id"],
                  "concept_ids": CHECKPOINTS[state["queue"]["current_checkpoint_id"]]["concept_ids"], "received_at": self.timestamp(),
                  "interpretation": "student_report_unassessed"}
        state["responses"].append(record)
        state["responses"] = state["responses"][-100:]
        state["runtime"]["response_projection"] = "latest_100_full_history_in_events"
        origin = self.context(state)
        telemetry = self.current_step(state)["telemetry"]
        if body.kind == "question":
            telemetry["help_request_count"] += 1
        elif body.kind in ("prediction", "observation", "explanation"):
            telemetry["answer_count"] += 1
        advanced = False
        if state.get('progression_mode') == 'screen_guided':
            for c in self.current_step(state)['criteria']:
                if body.kind in POLICY['responses'].get(c['criterion_id'], []):
                    c.update(state='satisfied', completion_basis='student_report_unassessed', evidence_ids=[record['id']], parameter_revision=state['workspace']['parameter_revision'])
            advanced = self.finish_guided(state)
        return self.save(state, "student_response", {**record, 'advanced': advanced}, "student", origin)

    async def check(self, lab_id, owner, body):
        state = self.load(lab_id, owner)
        self.expect(state, body.revision)
        if state["status"] != "active" or not self.current_step(state):
            raise HTTPException(409, "Resume the current lab before checking")
        if not self.analyzer.configured:
            raise HTTPException(503, "Configure GEMINI_API_KEY on the FastAPI server")
        if state["runtime"]["analysis_token"] is not None:
            raise HTTPException(409, "A check is already running for this lab")
        if state["runtime"].get("retry_at_ms", 0) > self.clock()*1000:
            return self.project(state)
        last = state["runtime"]["last_analysis_started"]
        if last is not None and self.clock() - last < CHECK_INTERVAL_SECONDS:
            raise HTTPException(429, "Wait three seconds between checks")
        capture = self.capture(state["workspace"]["capture_session_id"], owner)
        frame, pixels = capture["frame"], capture["pixels"]
        if capture["status"] != "sharing" or frame is None or pixels is None:
            raise HTTPException(409, "Share the attached model and wait for a frame")
        if frame["frame_id"] != body.frame_id:
            raise HTTPException(409, "Frame was replaced; select the latest received frame")
        if self.clock() - frame["server_received_unix"] > 6:
            raise HTTPException(409, "Frame is old; wait for another received frame")
        if body.view_revision != state["workspace"]["view_revision"] or frame["view_revision"] != body.view_revision:
            raise HTTPException(409, "View changed; capture a frame with the current revision")
        if hashlib.sha256(pixels).hexdigest() != frame["sha256"] or len(pixels) != frame["byte_count"]:
            raise HTTPException(409, "Trusted frame provenance does not match pixels")
        frame = copy.deepcopy(frame)  # immutable source even while new frames arrive
        state["runtime"]["capture_status"] = "sharing"
        state["runtime"]["analysis_attempts"] += 1
        state["runtime"]["last_analysis_started"] = self.clock()
        token = new_id()
        state["runtime"]["analysis_token"] = token
        state["runtime"]["analysis_status"] = "checking"
        self.current_step(state)["telemetry"]["analysis_attempts"] += 1
        self.save(state, "analysis_started", {"frame_id": frame["frame_id"]})
        admitted = self.context(state)
        cp = CHECKPOINTS[admitted["checkpoint_id"]]
        failure, result, retry_at_ms, metrics = None, None, None, {}
        started=time.monotonic()
        try:
            async with asyncio.timeout(20):
                async with self.provider_slots:
                    output=await self.analyzer.analyze(pixels, cp, copy.deepcopy(state))
                    metrics=getattr(output,"metrics",{})
                    result=validate_result(output, cp)
        except AnalysisFailure as exc:
            failure = str(exc)
            retry_at_ms = exc.retry_at_ms
        except TimeoutError:
            failure = "provider_timeout_or_network_error"
        except asyncio.CancelledError:
            current = self.load(lab_id, owner)
            if current["runtime"]["analysis_token"] == token:
                current["runtime"].update(analysis_token=None, analysis_status="cancelled")
                self.save(current, "analysis_cancelled", {"frame_id": frame["frame_id"]})
            raise
        current = self.load(lab_id, owner)
        # Recheck after the provider await; results cannot migrate to another visit/view.
        if current["revision"] != state["revision"] or current["runtime"]["analysis_token"] != token:
            if current["runtime"]["analysis_token"] == token:
                current["runtime"].update(analysis_token=None, analysis_status="discarded")
                self.save(current, "analysis_discarded", {"reason": "stale_context", "admitted_context": admitted})
            raise HTTPException(409, "Lab context changed during analysis; result discarded")
        attached = self.capture(current["workspace"]["capture_session_id"], owner)
        if attached["status"] != "sharing" or self.clock() - frame["server_received_unix"] > FRAME_AGE_SECONDS:
            self.invalidate(current, "capture_disconnected_or_frame_expired")
            self.save(current, "analysis_discarded", {"admitted_context": admitted})
            raise HTTPException(409, "Capture changed or analysed frame expired; check again")
        current["runtime"]["analysis_token"] = None
        current["runtime"]["last_analysis_timing"]={**metrics,"frame_id":frame["frame_id"],"status":"failed" if failure else "available","total_ms":round((time.monotonic()-started)*1000),"received_to_result_ms":round((self.clock()-frame["server_received_unix"])*1000)}
        if failure:
            current["runtime"].update(analysis_status="waiting_for_provider", analysis_error=failure, retry_at_ms=retry_at_ms or int((self.clock()+10)*1000))
            self.current_step(current)["telemetry"]["analysis_failures"] += 1
            return self.save(current, "analysis_failed", {"error": failure, "frame_id": frame["frame_id"]})
        observation_id = new_id()
        deadline = min(self.clock() + 8, frame["server_received_unix"] + FRAME_AGE_SECONDS)
        candidate = {**result, "observation_id": observation_id, "source_frame": frame, "admitted_context": admitted,
                     "admitted_at": self.timestamp(state["runtime"]["last_analysis_started"]), "completed_at": self.timestamp(),
                     "model": getattr(self.analyzer, "model", "injected_test_adapter"),
                     "prompt_version": getattr(self.analyzer, "prompt_version", "injected_test_adapter"),
                     "frame_handle": {"handle_id": observation_id, "expires_at": self.timestamp(deadline), "media_type": "image/jpeg", "access_policy": "same_owner_ephemeral"}}
        current["runtime"].update(candidate=candidate, analysis_status="available")
        current["runtime"].pop("analysis_error", None)
        current["runtime"].pop("retry_at_ms", None)
        current["observation"] = {"observation_id": observation_id, "source_frame_id": frame["frame_id"],
            "view_revision": admitted["view_revision"], "status": "available", "source_received_at": frame["server_received_at"], "age_ms": 0}
        advanced = self.apply_guided(current, candidate)
        value = self.save(current, "analysis_completed", {"candidate": candidate, 'advanced': advanced}, origin=admitted)
        if not advanced:
            self.images[lab_id] = (observation_id, pixels)
        return value

    def review(self, lab_id, owner, body):
        state = self.load(lab_id, owner)
        self.expect(state, body.revision)
        cp_id = state["queue"]["current_checkpoint_id"]
        step = self.current_step(state)
        candidate = state["runtime"]["candidate"]
        if state["status"] != "active" or not step or state["runtime"]["capture_status"] != "sharing" or not candidate:
            raise HTTPException(409, "Resume sharing and check this step before review")
        context = self.context(state)
        if any(context[k] != candidate["admitted_context"][k] for k in context if k != "lab_revision"):
            raise HTTPException(409, "Checked evidence belongs to an older context")
        if self.clock() - candidate["source_frame"]["server_received_unix"] > FRAME_AGE_SECONDS or lab_id not in self.images:
            raise HTTPException(409, "Checked image expired; check this step again")
        if state["workspace"]["condition"] != expected_condition(cp_id):
            raise HTTPException(409, "Declare this checkpoint's expected condition and check again")
        ids = set(body.criterion_ids)
        if len(ids) != len(body.criterion_ids) or not ids <= {c["criterion_id"] for c in step["criteria"]} or len(body.review_note.strip()) < 8:
            raise HTTPException(422, "Select unique current criteria and describe reviewed evidence")
        required_kinds = {"observation_record": {"observation"}, "phase_fault_observation": {"prediction", "observation"}, "explanation": {"explanation"}}
        for cid in ids:
            kinds = required_kinds.get(cid.split(":")[-1])
            if kinds and not any(r["kind"] in kinds and r["visit_id"] == state["current_visit_id"] for r in state["responses"]):
                raise HTTPException(422, "Record the required observation or explanation for this visit")
        origin = self.context(state)
        self.account_time(state)
        evidence = {"evidence_id": new_id(), "origin": "operator_review", "synthetic": False, "context": origin,
                    "observation_id": candidate["observation_id"], "frame_id": candidate["source_frame"]["frame_id"],
                    "sha256": candidate["source_frame"]["sha256"], "reviewed_at": self.timestamp(),
                    "review_note": body.review_note.strip(), "criterion_ids": body.criterion_ids}
        state["evidence"].append(evidence)
        for c in step["criteria"]:
            if c["criterion_id"] in ids:
                c.update(state="satisfied", parameter_revision=state["workspace"]["parameter_revision"])
                if state.get('progression_mode') == 'screen_guided':
                    c['completion_basis'] = 'student_confirmation_unassessed'
                c["evidence_ids"].append(evidence["evidence_id"])
        completed = all(c["state"] == "satisfied" for c in step["criteria"])
        if completed:
            step["status"] = "done"
            if state.get('progression_mode') == 'screen_guided':
                step['completion_basis'] = 'screen_inferred_or_student_report'
                step['assessment_status'] = 'unassessed'
            state["queue"]["done_checkpoint_ids"].append(cp_id)
            state["queue"]["current_checkpoint_id"] = state["queue"]["upcoming_checkpoint_ids"].pop(0) if state["queue"]["upcoming_checkpoint_ids"] else None
            next_step = self.current_step(state)
            if next_step:
                next_step["status"] = "in_progress"
                next_step["current_visit_id"] = new_id()
                next_step["visits"].append(next_step["current_visit_id"])
                next_step["attempt_count"] += 1
                state["current_visit_id"] = next_step["current_visit_id"]
            else:
                state["current_visit_id"] = None
                state["status"] = "completed"
            if cp_id == ORDER[0]:
                state["workspace"]["confirmed"] = True
            self.invalidate(state, "checkpoint_changed")
        return self.save(state, "checkpoint_completed" if completed else "criteria_reviewed", {"evidence": evidence}, "student", origin)

    def image(self, lab_id, owner, handle=None):
        state = self.load(lab_id, owner)
        candidate = state["runtime"]["candidate"]
        saved = self.images.get(lab_id)
        valid = candidate and saved and saved[0] == candidate["observation_id"] and state["status"] == "active" and state["runtime"]["capture_status"] == "sharing"
        if not valid or self.clock() - candidate["source_frame"]["server_received_unix"] > FRAME_AGE_SECONDS:
            raise HTTPException(410, "Checked pixels unavailable; capture/check a new frame")
        if handle is not None and (handle != saved[0] or self.clock() >= datetime.fromisoformat(candidate["frame_handle"]["expires_at"]).timestamp()):
            raise HTTPException(410, "Frame handle expired, replaced or invalidated")
        return saved[1], candidate
