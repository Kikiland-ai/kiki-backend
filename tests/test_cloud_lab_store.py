"""Cloud lab contract tests; real emulator execution is explicitly opt-in.

Offline transaction double proves domain boundary/rollback invariants, not distributed
Firestore durability. Set FIRESTORE_EMULATOR_HOST to exercise independent real clients.
"""

import copy
import os
import subprocess
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException

from contracts.lab_tracking import StartLab, ContextChange
from prototypes.cloud_lab.domain import CloudLabService
from prototypes.cloud_lab.store import CloudLabCreateKeys, FirestoreLabStore, run_atomic


BODY = StartLab(model_name="cloud_contract_fixture", operator_trial=True)


class Snapshot:
    def __init__(self, ref, value):
        self.reference = ref
        self.value = copy.deepcopy(value)
        self.exists = value is not None

    def to_dict(self):
        return copy.deepcopy(self.value)


class Reference:
    def __init__(self, client, path):
        self.client, self.path = client, path

    def get(self, transaction=None):
        return Snapshot(self, (transaction.values if transaction else self.client.values).get(self.path))

    def collection(self, name):
        return Query(self.client, self.path + "/" + name)

    def delete(self):
        self.client.values.pop(self.path, None)


class Query:
    def __init__(self, client, path, filters=(), maximum=None, sort=None):
        self.client, self.path, self.filters = client, path, filters
        self.maximum, self.sort = maximum, sort

    def document(self, name):
        return Reference(self.client, self.path + "/" + name)

    def where(self, field, operation, value):
        return Query(self.client, self.path, (*self.filters, (field, operation, value)), self.maximum, self.sort)

    def order_by(self, field):
        return Query(self.client, self.path, self.filters, self.maximum, field)

    def limit(self, value):
        return Query(self.client, self.path, self.filters, value, self.sort)

    def stream(self, transaction=None):
        values = transaction.values if transaction else self.client.values
        result = []
        for path, value in values.items():
            if not path.startswith(self.path + "/") or "/" in path[len(self.path) + 1:]:
                continue
            matches = all(value.get(f) == v if op == "==" else value.get(f, 0) > v for f, op, v in self.filters)
            if matches:
                result.append(Snapshot(Reference(self.client, path), value))
        if self.sort:
            result.sort(key=lambda s: s.to_dict()[self.sort])
        return iter(result[:self.maximum] if self.maximum is not None else result)


class Transaction:
    def __init__(self, values, fail_at=None):
        self.values, self.fail_at, self.writes = values, fail_at, 0

    def create(self, ref, value):
        if ref.path in self.values:
            raise RuntimeError("duplicate document")
        self.set(ref, value)

    def set(self, ref, value):
        self.writes += 1
        self.values[ref.path] = copy.deepcopy(value)
        if self.fail_at == self.writes:
            raise RuntimeError("injected transaction failure")


class MemoryClient:
    def __init__(self):
        self.values = {}
        self.lock = threading.RLock()
        self.fail_at = None

    def collection(self, name):
        return Query(self, name)

    def _run_transaction(self, operation):
        with self.lock:
            transaction = Transaction(copy.deepcopy(self.values), self.fail_at)
            result = operation(transaction)
            self.values = transaction.values
            return result


class Contract:
    def capture_row(self, client, status="sharing", fence=2):
        ref = client.collection(self.prefix + "_captures").document("capture-fixture")
        row = {"owner": "fb:fixture", "status": status, "fence": fence,
               "producer": "replacement" if status == "sharing" else None,
               "lease_until": 4_000_000_000 if status == "sharing" else 0,
               "latest": {"view_revision": 1}}
        run_atomic(client, lambda transaction: transaction.set(ref, row))

    def service(self, client=None):
        store = FirestoreLabStore(client or self.client, self.prefix)
        analyzer = SimpleNamespace(configured=False)
        return CloudLabService(store, None, analyzer), CloudLabCreateKeys(store)

    def create(self, lab, keys, owner="fb:fixture", key="first", digest="body-hash"):
        return keys.start(lab, owner, key, digest, BODY)

    def assert_http(self, status, call):
        with self.assertRaises(HTTPException) as error:
            call()
        self.assertEqual(error.exception.status_code, status)

    def test_two_clients_retry_one_lab_and_first_event(self):
        pairs = [self.service(client) for client in self.clients]
        gate = threading.Barrier(2)
        def start(pair):
            gate.wait(10)
            return self.create(*pair)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(start, pairs))
        ids = {state["lab_session_id"] for state, _ in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(sorted(replay for _, replay in results), [False, True])
        lab_id = ids.pop()
        self.assertEqual(len(pairs[1][0].store.events(lab_id, "fb:fixture")), 1)
        restarted, keys = self.service(self.clients[1])
        replay, replayed = self.create(restarted, keys)
        self.assertTrue(replayed)
        self.assertEqual(replay["lab_session_id"], lab_id)

    def test_revision_conflict_has_no_extra_event_and_owner_is_hidden(self):
        lab, keys = self.service()
        created, _ = self.create(lab, keys)
        lab_id = created["lab_session_id"]
        self.assertNotIn("owner_id", created)
        second, _ = self.service(self.clients[1])
        old = second.load(lab_id, "fb:fixture")
        lab.change(lab_id, "fb:fixture", ContextChange(revision=1, action="pause"))
        stale = copy.deepcopy(old)
        stale["revision"] = 2
        self.assert_http(409, lambda: second.store.save(stale, 1, second.event(stale, "stale_write")))
        self.assertEqual([v["event_sequence"] for v in lab.store.events(lab_id, "fb:fixture")], [1, 2])
        self.assert_http(404, lambda: lab.load(lab_id, "fb:foreign"))
        self.assert_http(404, lambda: lab.store.events(lab_id, "fb:foreign"))
        self.assert_http(404, lambda: lab.store.delete(lab_id, "fb:foreign"))

    def test_body_conflict_owner_scope_tombstone_and_no_resurrection(self):
        lab, keys = self.service()
        state, _ = self.create(lab, keys)
        self.assert_http(409, lambda: self.create(lab, keys, digest="different"))
        other, _ = self.create(lab, keys, owner="fb:other")
        self.assertNotEqual(state["lab_session_id"], other["lab_session_id"])
        lab.store.delete(state["lab_session_id"], "fb:fixture")
        self.assert_http(404, lambda: self.create(lab, keys))
        self.assertEqual(lab.store.list("fb:fixture"), [])
        self.assertEqual(len(lab.store.all()), 1)

    def test_new_worker_does_not_disconnect_other_active_labs(self):
        lab, keys = self.service()
        created, _ = self.create(lab, keys)
        state = lab.load(created["lab_session_id"], "fb:fixture")
        state["runtime"]["capture_status"] = "sharing"
        state["workspace"]["capture_session_id"] = "active-capture"
        lab.save(state, "fixture_capture_attached")
        second, _ = self.service(self.clients[1])
        unchanged = second.load(state["lab_session_id"], "fb:fixture")
        self.assertEqual(unchanged["runtime"]["capture_status"], "sharing")
        self.assertEqual(unchanged["revision"], 2)
        second.capture_changed("unrelated-capture", "disconnected")
        self.assertEqual(second.load(state["lab_session_id"], "fb:fixture")["revision"], 2)
        second.capture_changed("active-capture", "disconnected")
        self.assertEqual(second.load(state["lab_session_id"], "fb:fixture")["revision"], 3)

    def test_delayed_disconnect_hint_preserves_authoritative_replacement_candidate(self):
        lab, keys = self.service()
        created, _ = self.create(lab, keys)
        state = lab.load(created["lab_session_id"], "fb:fixture")
        state["workspace"]["capture_session_id"] = "capture-fixture"
        state["runtime"]["capture_status"] = "sharing"
        state["runtime"]["candidate"] = {"observation_id": "replacement-observation",
                                          "source_frame": {"server_received_unix": lab.clock()}}
        lab.save(state, "fixture_replacement_checked")
        self.capture_row(self.clients[1])
        observer = CloudLabService(lab.store, None, SimpleNamespace(configured=False),
                                   capture_snapshot=lab.store.capture_snapshot)
        observer.capture_changed("capture-fixture", "disconnected", view_revision=99)
        actual = lab.store.load(state["lab_session_id"], "fb:fixture")
        self.assertEqual(actual["revision"], state["revision"])
        self.assertEqual(actual["runtime"]["candidate"]["observation_id"], "replacement-observation")
        self.assertEqual(actual["workspace"]["view_revision"], 1)

    def test_capture_replacement_after_snapshot_is_rejected_in_lab_transaction(self):
        lab, keys = self.service()
        created, _ = self.create(lab, keys)
        state = lab.load(created["lab_session_id"], "fb:fixture")
        state["workspace"]["capture_session_id"] = "capture-fixture"
        lab.save(state, "fixture_capture_attached")
        self.capture_row(self.clients[0], status="disconnected", fence=1)
        guard = lab.store.capture_snapshot("capture-fixture", "fb:fixture")["guard"]
        # Another real client replaces the producer after the callback reads its
        # snapshot but before its lab projection/event transaction begins.
        self.capture_row(self.clients[1], status="sharing", fence=2)
        state["revision"] += 1
        event = lab.event(state, "obsolete_disconnect")
        self.assert_http(409, lambda: lab.store.save(state, state["revision"] - 1, event, capture_guard=guard))
        actual = lab.store.load(state["lab_session_id"], "fb:fixture")
        self.assertEqual(actual["revision"], state["revision"] - 1)
        self.assertEqual(len(lab.store.events(state["lab_session_id"], "fb:fixture")), 2)


class OfflineCloudLabTests(Contract, unittest.TestCase):
    def setUp(self):
        self.client = MemoryClient()
        self.clients = [self.client, self.client]
        self.prefix = "contract"

    def test_failure_after_each_create_write_rolls_back_all_documents(self):
        for position in (1, 2, 3):
            self.client.fail_at = position
            lab, keys = self.service()
            with self.assertRaisesRegex(RuntimeError, "injected transaction failure"):
                self.create(lab, keys)
            self.assertEqual(self.client.values, {})
        self.client.fail_at = None
        lab, keys = self.service()
        self.assertFalse(self.create(lab, keys)[1])

    def test_projection_failure_happens_before_transaction(self):
        lab, keys = self.service()
        def fail(state):
            raise RuntimeError("projection failure")
        lab.project = fail
        with self.assertRaisesRegex(RuntimeError, "projection failure"):
            self.create(lab, keys)
        self.assertEqual(self.client.values, {})

    def test_invalid_revision_event_is_rejected_before_write(self):
        lab, keys = self.service()
        state, _ = self.create(lab, keys)
        raw = lab.load(state["lab_session_id"], "fb:fixture")
        raw["revision"] = 4
        with self.assertRaisesRegex(ValueError, "exactly one"):
            lab.store.save(raw, 1, lab.event(raw, "bad_revision"))

    def test_replacement_recovers_only_expired_analysis_and_producer(self):
        lab, keys = self.service()
        lab.clock = lambda: 1000
        result, _ = self.create(lab, keys)
        state = lab.load(result["lab_session_id"], "fb:fixture")
        state["workspace"]["capture_session_id"] = "expired-capture"
        state["runtime"].update(capture_status="sharing", analysis_token="dead-worker",
                                 last_analysis_started=1)
        lab.save(state, "fixture_started")
        replacement = CloudLabService(lab.store, lambda cid, owner: {"status": "disconnected"},
                                      SimpleNamespace(configured=False), clock=lambda: 1050)
        recovered = replacement.load(state["lab_session_id"], "fb:fixture")
        self.assertIsNone(recovered["runtime"]["analysis_token"])
        self.assertEqual(recovered["runtime"]["capture_status"], "disconnected")
        self.assertEqual(recovered["revision"], 3)
        timing = replacement.current_step(recovered)["timing"]
        self.assertEqual(timing["tracking_active_ms"], 0)
        self.assertEqual(timing["disconnected_ms"], 50_000)
        self.assertEqual(replacement.load(state["lab_session_id"], "fb:fixture")["revision"], 3)

    def test_fresh_analysis_survives_worker_read_until_lease_timeout(self):
        lab, keys = self.service()
        lab.clock = lambda: 100
        result, _ = self.create(lab, keys)
        state = lab.load(result["lab_session_id"], "fb:fixture")
        state["runtime"].update(analysis_token="running", last_analysis_started=90)
        lab.save(state, "fixture_started")
        self.assertEqual(lab.load(state["lab_session_id"], "fb:fixture")["runtime"]["analysis_token"], "running")
        lab.clock = lambda: 121
        self.assertIsNone(lab.load(state["lab_session_id"], "fb:fixture")["runtime"]["analysis_token"])

    def test_stale_invalidation_cannot_delete_another_workers_image(self):
        lab, keys = self.service()
        result, _ = self.create(lab, keys)
        lab_id = result["lab_session_id"]
        stale = lab.load(lab_id, "fb:fixture")
        fresh = lab.load(lab_id, "fb:fixture")
        lab.save(fresh, "winning_write")
        lab.images[lab_id] = ("new-observation", b"fresh-jpeg-fixture")
        stale["runtime"]["candidate"] = {"observation_id": "old-observation"}
        lab.invalidate(stale, "pause")
        self.assert_http(409, lambda: lab.save(stale, "losing_write"))
        self.assertEqual(lab.images[lab_id][0], "new-observation")

    def test_successful_old_invalidation_preserves_newer_image_generation(self):
        lab, keys = self.service()
        result, _ = self.create(lab, keys)
        lab_id = result["lab_session_id"]
        state = lab.load(lab_id, "fb:fixture")
        state["runtime"]["candidate"] = {"observation_id": "old-observation"}
        lab.images[lab_id] = ("new-observation", b"fresh-jpeg-fixture")
        lab.invalidate(state, "pause")
        lab.save(state, "old_invalidation")
        self.assertEqual(lab.images[lab_id][0], "new-observation")
        self.assertNotIn("_cloud_image_invalidation_id", lab.store.load(lab_id, "fb:fixture"))

    def test_status_reconciliation_does_not_download_frame_chunks(self):
        lab, keys = self.service()
        result, _ = self.create(lab, keys)
        lab_id = result["lab_session_id"]
        state = lab.load(lab_id, "fb:fixture")
        state["workspace"]["capture_session_id"] = "live-capture"
        state["runtime"]["capture_status"] = "sharing"
        lab.save(state, "fixture_capture_attached")
        def pixels_forbidden(*args):
            raise AssertionError("Status reconciliation must not read frame bytes")
        replacement = CloudLabService(lab.store, pixels_forbidden, SimpleNamespace(configured=False),
                                      capture_status=lambda sid, owner: {"status": "sharing"})
        self.assertEqual(replacement.load(lab_id, "fb:fixture")["revision"], 2)


@unittest.skipUnless(os.getenv("FIRESTORE_EMULATOR_HOST"), "requires real Firestore emulator")
class EmulatorCloudLabTests(Contract, unittest.TestCase):
    def setUp(self):
        from google.cloud import firestore
        from google.auth.credentials import AnonymousCredentials
        self.clients = [firestore.Client(project="kiki-cloud-contract", database="kiki-firedb",
                                         credentials=AnonymousCredentials()) for _ in range(2)]
        self.client = self.clients[0]
        self.prefix = "contract_" + uuid4().hex

    def tearDown(self):
        cleanup_contract(self.client, self.prefix)
        for client in self.clients:
            client.close()


def cleanup_contract(client, prefix):
    """Delete only this test's unique namespace, including its subcollections."""
    if not prefix.startswith("contract_"):
        raise ValueError("Refusing cleanup outside this contract namespace")
    for lab in client.collection(prefix + "_labs").stream():
        for event in lab.reference.collection("events").stream():
            event.reference.delete()
        lab.reference.delete()
    for receipt in client.collection(prefix + "_lab_create_receipts").stream():
        receipt.reference.delete()
    for capture in client.collection(prefix + "_captures").stream():
        capture.reference.delete()


@unittest.skipUnless(os.getenv("KIKI_CLOUD_CONTRACT") == "1", "requires authorized real named-DB contract")
class LiveNamedDatabaseTests(Contract, unittest.TestCase):
    def setUp(self):
        from google.cloud import firestore
        from google.oauth2.credentials import Credentials
        # Token remains solely in this process; never log, save or set an env var.
        result = subprocess.run(["gcloud.cmd", "auth", "print-access-token",
                                 "--account=arpanvihan5@gmail.com", "--quiet"],
                                check=True, capture_output=True, text=True, timeout=30,
                                env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
        credentials = Credentials(result.stdout.strip())
        self.clients = [firestore.Client(project="kiki-512012", database="kiki-firedb",
                                         credentials=credentials) for _ in range(2)]
        self.client = self.clients[0]
        self.prefix = "contract_fullcloud_" + uuid4().hex

    def tearDown(self):
        try:
            cleanup_contract(self.client, self.prefix)
        finally:
            for client in self.clients:
                client.close()


if __name__ == "__main__":
    unittest.main()
