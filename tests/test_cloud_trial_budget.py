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
            app = create_app(client=MemoryClient(), analyzer=SimpleNamespace(configured=False), proxy_secret="x" * 32)
            with TestClient(app) as client:
                self.assertEqual(client.get("/health").json()["trial_check_limit"], 5)


if __name__ == "__main__":
    unittest.main()
