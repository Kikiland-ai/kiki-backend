"""Cloud composition of frozen lab rules without SQLite lifecycle side effects."""

import asyncio
import time

from fastapi import HTTPException

from prototypes.lab_tracking.service import LabService


class CloudLabService(LabService):
    def __init__(self, store, capture, analyzer, images=None, clock=time.time, *, capture_status=None):
        # Deliberately do not call LabService.__init__: it creates SQLite, binds an
        # SQL provider and invalidates *all* noncompleted labs on each worker start.
        # The cloud analyzer must arrive with its shared provider configured.
        self.store = store
        self.capture = capture
        self.capture_status = capture_status if capture_status is not None else capture
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
        invalidated_image = state.pop("_cloud_image_invalidation_id", None)
        result = super().save(state, kind, payload, actor, origin)
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
                try:
                    current = self.capture_status(capture_id, owner)
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
                state = self.load(snapshot["lab_session_id"], snapshot["owner_id"])
                if state["workspace"]["capture_session_id"] != capture_id or state["status"] == "completed":
                    break
                changed_view = view_revision is not None and view_revision > state["workspace"]["view_revision"]
                if state["runtime"]["capture_status"] == status and not changed_view:
                    break
                self.account_time(state)
                state["runtime"]["capture_status"] = status
                if changed_view:
                    state["workspace"]["view_revision"] = view_revision
                reason = "view_changed" if changed_view else f"capture_{status}"
                self.invalidate(state, reason)
                try:
                    self.save(state, reason)
                    break
                except HTTPException as exc:
                    if exc.status_code != 409 or attempt == 2:
                        raise


def create_domain(store, capture, analyzer, *, images=None, clock=time.time, capture_status=None):
    return CloudLabService(store, capture, analyzer, images=images, clock=clock, capture_status=capture_status)
