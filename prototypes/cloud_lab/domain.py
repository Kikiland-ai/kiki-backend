"""Cloud composition of frozen lab rules without SQLite lifecycle side effects."""

import asyncio
import time

from fastapi import HTTPException

from prototypes.lab_tracking.service import LabService


class CloudLabService(LabService):
    def __init__(self, store, capture, analyzer, images=None, clock=time.time, *, capture_status=None, capture_snapshot=None, trial_check_limit=None):
        # Deliberately do not call LabService.__init__: it creates SQLite, binds an
        # SQL provider and invalidates *all* noncompleted labs on each worker start.
        # The cloud analyzer must arrive with its shared provider configured.
        self.store = store
        self.capture = capture
        self.capture_status = capture_status if capture_status is not None else capture
        self.capture_snapshot = capture_snapshot
        if trial_check_limit is not None and (type(trial_check_limit) is not int or not 1 <= trial_check_limit <= 1000):
            raise ValueError("Trial check limit must be an integer from 1 to 1000")
        self.trial_check_limit = trial_check_limit
        self.analyzer = analyzer
        self.clock = clock
        self.images = images if images is not None else {}
        self.provider_slots = asyncio.Semaphore(4)

    def invalidate(self, state, reason):
        # Same frozen domain policy, with shared pixel deletion deferred until CAS
        # succeeds. A losing writer must not erase a newer worker's checked frame.
        candidate = state["runtime"].get("candidate")
        if candidate:
            state["_cloud_image_invalidation_id"] = candidate["observation_id"]
        state["runtime"]["candidate"] = None
        state["observation"] = None
        state["runtime"]["analysis_token"] = None
        state["runtime"]["analysis_status"] = "invalidated"
        state["runtime"]["invalidation_reason"] = reason
        if reason != "view_changed":
            state["auto_tracking"] = {}
            state["procedure_tracking"] = {}
            if reason not in ("pause", "resume", "server_restarted") and not reason.startswith("capture_"):
                state["procedure_history"] = {}
            for criterion in (self.current_step(state) or {}).get("criteria", []):
                if criterion.get("completion_basis") == "screen_inferred":
                    criterion.update(state="unknown", evidence_ids=[], completion_basis=None)

    def save(self, state, kind, payload=None, actor="system", origin=None):
        # Admission is persisted before the analyzer runs. Revision CAS serializes
        # concurrent workers at the final permitted check; rejected retries cannot
        # create a sixth event or dispatch another provider request.
        if (kind == "analysis_started" and self.trial_check_limit is not None
                and state["runtime"]["analysis_attempts"] > self.trial_check_limit):
            raise HTTPException(429, "The approved screen-check trial budget is exhausted")
        invalidated_image = state.pop("_cloud_image_invalidation_id", None)
        capture_guard = state.pop("_cloud_capture_guard", None)
        self.account_time(state)
        expected = state["revision"]
        state["revision"] += 1
        event = self.event(state, kind, payload, actor, origin)
        if capture_guard is None:
            self.store.save(state, expected, event)
        else:
            self.store.save(state, expected, event, capture_guard=capture_guard)
        result = self.project(state)
        if invalidated_image:
            if hasattr(self.images, "discard_if"):
                self.images.discard_if(state["lab_session_id"], invalidated_image)
            else:
                saved = self.images.get(state["lab_session_id"])
                if saved and saved[0] == invalidated_image:
                    self.images.pop(state["lab_session_id"], None)
        return result

    def load(self, lab_id, owner):
        """Recover only the requested lab using shared producer freshness.

        A replaced worker must not leave a permanent analysis token or count an
        expired producer as active capture. No other learner's labs are scanned.
        """
        for attempt in range(3):
            state = self.store.load(lab_id, owner)
            if state["status"] == "completed":
                return state
            capture_id = state["workspace"].get("capture_session_id")
            reason = None
            if capture_id and self.capture_status is not None:
                current = {}
                try:
                    current = (self.capture_snapshot or self.capture_status)(capture_id, owner)
                    status = current["status"]
                except HTTPException as exc:
                    if exc.status_code != 404:
                        raise
                    status = "disconnected"
                if state["runtime"]["capture_status"] != status:
                    # A lost lease leaves an unobserved interval. Conservatively
                    # classify that interval as disconnected, never continuous
                    # tracking across worker death or a missing producer.
                    if status != "sharing":
                        state["runtime"]["capture_status"] = status
                        self.account_time(state)
                    else:
                        self.account_time(state)
                        state["runtime"]["capture_status"] = status
                    reason = f"capture_{status}"
                    if current.get("guard") is not None:
                        state["_cloud_capture_guard"] = current["guard"]
            runtime = state["runtime"]
            if not reason and runtime.get("analysis_token") and self.clock() - (runtime.get("last_analysis_started") or 0) > 30:
                reason = "analysis_worker_expired"
            if not reason:
                return state
            self.invalidate(state, reason)
            try:
                self.save(state, reason)
                return state
            except HTTPException as exc:
                if exc.status_code != 409 or attempt == 2:
                    raise

    def capture_changed(self, capture_id, status, view_revision=None):
        # Only the affected capture's labs are candidates. Shared revision CAS
        # prevents a stale callback overwriting a newer worker's student mutation.
        for snapshot in self.store.by_capture(capture_id):
            if snapshot["status"] == "completed":
                continue
            for attempt in range(3):
                state = self.store.load(snapshot["lab_session_id"], snapshot["owner_id"])
                if state["workspace"]["capture_session_id"] != capture_id or state["status"] == "completed":
                    break
                current = self.capture_snapshot(capture_id, state["owner_id"]) if self.capture_snapshot is not None else None
                authoritative_status = current["status"] if current is not None else status
                authoritative_view = current.get("view_revision") if current is not None else view_revision
                changed_view = authoritative_view is not None and authoritative_view > state["workspace"]["view_revision"]
                if state["runtime"]["capture_status"] == authoritative_status and not changed_view:
                    break
                self.account_time(state)
                state["runtime"]["capture_status"] = authoritative_status
                if changed_view:
                    state["workspace"]["view_revision"] = authoritative_view
                reason = "view_changed" if changed_view else f"capture_{authoritative_status}"
                if current is not None:
                    state["_cloud_capture_guard"] = current["guard"]
                self.invalidate(state, reason)
                try:
                    self.save(state, reason)
                    break
                except HTTPException as exc:
                    if exc.status_code != 409 or attempt == 2:
                        raise


def create_domain(store, capture, analyzer, *, images=None, clock=time.time, capture_status=None, capture_snapshot=None, trial_check_limit=None):
    return CloudLabService(store, capture, analyzer, images=images, clock=clock, capture_status=capture_status, capture_snapshot=capture_snapshot, trial_check_limit=trial_check_limit)
