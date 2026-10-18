"""Trial admission cap: actual domain checks with synthetic analyzer, no model IO."""
import hashlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from contracts.lab_tracking import AttachCapture, CheckFrame, StartLab
from prototypes.cloud_lab.domain import CloudLabService
from prototypes.cloud_lab.runtime import create_app
from prototypes.cloud_lab.store import FirestoreLabStore
from test_cloud_lab_store import MemoryClient
from test_lab_tracking import FakeAnalyzer


class TrialBudgetTests(unittest.IsolatedAsyncioTestCase):
    def budget_lab(self, client, limit=5, owner="fixture-owner"):
        store = FirestoreLabStore(client, trial_check_limit=limit)
        lab = CloudLabService(store, None, SimpleNamespace(configured=False), trial_check_limit=limit)
        created = lab.start(owner, StartLab(model_name="fixture", operator_trial=True))
        return lab, lab.load(created["lab_session_id"], owner)

    def admit(self, lab, state):
        state["runtime"]["analysis_attempts"] += 1
        return lab.save(state, "analysis_started")

    def test_shared_budget_survives_new_labs_owners_and_store_replacement(self):
        client = MemoryClient()
        for index in range(5):
            lab, state = self.budget_lab(client, owner=f"owner-{index}")
            self.admit(lab, state)
        replacement, state = self.budget_lab(client, owner="new-owner-after-restart")
        before = replacement.store.load(state["lab_session_id"], state["owner_id"])
        with self.assertRaises(HTTPException) as error:
            self.admit(replacement, state)
        self.assertEqual(error.exception.status_code, 429)
        self.assertEqual(replacement.store.load(state["lab_session_id"], state["owner_id"]), before)
        self.assertEqual(replacement.store.trial_budget.get().to_dict()["count"], 5)

    def test_failed_revision_and_transaction_rollback_do_not_consume_slot(self):
        client = MemoryClient()
        lab, state = self.budget_lab(client)
        stale = lab.load(state["lab_session_id"], state["owner_id"])
        lab.save(state, "winning_mutation")
        with self.assertRaises(HTTPException) as error:
            self.admit(lab, stale)
        self.assertEqual(error.exception.status_code, 409)
        self.assertFalse(lab.store.trial_budget.get().exists)
        for position in (1, 2, 3):
            current = lab.load(state["lab_session_id"], state["owner_id"])
            client.fail_at = position
            with self.assertRaisesRegex(RuntimeError, "injected transaction failure"):
                self.admit(lab, current)
            self.assertFalse(lab.store.trial_budget.get().exists)
        client.fail_at = None
        self.admit(lab, lab.load(state["lab_session_id"], state["owner_id"]))
        self.assertEqual(lab.store.trial_budget.get().to_dict()["count"], 1)

    def test_changed_limit_fails_closed_and_unset_does_not_create_budget(self):
        client = MemoryClient()
        lab, state = self.budget_lab(client)
        self.admit(lab, state)
        other, state = self.budget_lab(client, limit=6)
        with self.assertRaises(HTTPException) as error:
            self.admit(other, state)
        self.assertEqual(error.exception.status_code, 429)
        self.assertEqual(lab.store.trial_budget.get().to_dict()["count"], 1)
        normal, state = self.budget_lab(MemoryClient(), limit=None)
        self.admit(normal, state)
        self.assertFalse(normal.store.trial_budget.get().exists)

    async def exercise(self, limit, count):
        now = [1000.0]
        pixels = b"synthetic-approved-budget-fixture"
        capture = {"status": "sharing", "frame": None, "pixels": pixels}
        analyzer = FakeAnalyzer()
        store = FirestoreLabStore(MemoryClient())
        lab = CloudLabService(store, lambda sid, owner: capture, analyzer,
                              clock=lambda: now[0], trial_check_limit=limit)
        state = lab.start("fixture-owner", StartLab(model_name="fixture", operator_trial=True))
        lab_id = state["lab_session_id"]
        state = lab.attach(lab_id, "fixture-owner", AttachCapture(revision=state["revision"], capture_session_id="capture"))
        for sequence in range(1, count + 1):
            now[0] += 4
            capture["frame"] = {"frame_id": f"capture:1:{sequence}", "sha256": hashlib.sha256(pixels).hexdigest(),
                                "server_received_unix": now[0], "server_received_at": lab.timestamp(),
                                "byte_count": len(pixels), "view_revision": 1}
            before = store.load(lab_id, "fixture-owner")
            request = CheckFrame(revision=before["revision"], frame_id=capture["frame"]["frame_id"], view_revision=1)
            if limit is not None and sequence > limit:
                with self.assertRaises(HTTPException) as error:
                    await lab.check(lab_id, "fixture-owner", request)
                self.assertEqual(error.exception.status_code, 429)
                self.assertEqual(store.load(lab_id, "fixture-owner"), before)
            else:
                state = await lab.check(lab_id, "fixture-owner", request)
        expected = min(limit, count) if limit is not None else count
        self.assertEqual(len(analyzer.calls), expected)
        events = store.events(lab_id, "fixture-owner")
        self.assertEqual(sum(event["event_type"] == "analysis_started" for event in events), expected)

    async def test_five_checks_then_retries_have_no_analyzer_call_or_store_write(self):
        await self.exercise(5, 7)

    async def test_unset_limit_preserves_more_than_five_checks(self):
        await self.exercise(None, 7)

    def test_runtime_strict_env_and_health(self):
        for value in ("", "0", "-1", "1.0", " 5", "05", "1001", "true"):
            with self.subTest(value=value), patch.dict(os.environ, {"KIKI_TRIAL_MAX_CHECKS": value}):
                with self.assertRaisesRegex(RuntimeError, "KIKI_TRIAL_MAX_CHECKS"):
                    create_app(client=MemoryClient(), analyzer=SimpleNamespace(configured=False), proxy_secret="x" * 32)
        with patch.dict(os.environ, {"KIKI_TRIAL_MAX_CHECKS": "5"}):
            oversized = SimpleNamespace(configured=True, provider=SimpleNamespace(keys=[object() for _ in range(4)]))
            with self.assertRaisesRegex(RuntimeError, "at most three"):
                create_app(client=MemoryClient(), analyzer=oversized, proxy_secret="x" * 32)
            app = create_app(client=MemoryClient(), analyzer=SimpleNamespace(configured=False), proxy_secret="x" * 32)
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").json()["trial_check_limit"], 5)


if __name__ == "__main__":
    unittest.main()
