"""Contract/lifecycle tests for actual binary frame receipt, without a vision model."""

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from PIL import Image

from prototypes.screen_capture.server import COOKIE, create_app


class ScreenCaptureTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.directory.name))
        self.client = TestClient(self.app)
        self.client.get("/")
        self.headers = {"origin": "http://testserver"}
        self.sid = self.client.post("/screen-sessions", headers=self.headers).json()["session_id"]
        image = io.BytesIO()
        Image.new("RGB", (96, 54), (20, 90, 150)).save(image, format="JPEG")
        self.image = image.getvalue()
        self.meta = {"type": "frame", "capture_epoch": 1, "sequence": 1,
                     "captured_elapsed_ms": 10, "width": 96, "height": 54,
                     "source_width": 96, "source_height": 54,
                     "byte_count": len(self.image), "mime_type": "image/jpeg"}

    def tearDown(self):
        self.client.close()
        self.app.state.store.db.close()
        self.app.state.lab.store.db.close()
        self.directory.cleanup()

    def connect(self):
        return self.client.websocket_connect(f"/screen-sessions/{self.sid}/stream", headers=self.headers)

    def start(self, ws):
        self.assertEqual(ws.receive_json()["type"], "connected")
        ws.send_json({"type": "capture_started"})
        self.assertEqual(ws.receive_json()["observation"]["capture_status"], "sharing")

    def send(self, ws, meta=None, image=None):
        ws.send_json(meta or self.meta)
        ws.send_bytes(self.image if image is None else image)
        return ws.receive_json()

    def test_real_image_and_provenance_then_stop(self):
        with self.connect() as ws:
            self.start(ws)
            ack = self.send(ws)
            self.assertEqual(ack["type"], "ack")
            snapshot = ack["observation"]
            self.assertEqual(snapshot["received_frame_count"], 1)
            self.assertEqual(snapshot["observation"]["analysis_status"], "not_enabled")
            self.assertIsNone(snapshot["observation"]["summary"])
            frame = snapshot["observation"]["latest_frame"]
            self.assertEqual(frame["sha256"], hashlib.sha256(self.image).hexdigest())
            response = self.client.get(f"/screen-sessions/{self.sid}/frame")
            self.assertEqual(response.content, self.image)
            self.assertEqual(response.headers["content-type"], "image/jpeg")
            events = self.client.get(f"/screen-sessions/{self.sid}/events").json()["events"]
            self.assertEqual([e["type"] for e in events], ["session_created", "capture_started", "frame_received"])
            ws.send_json({"type": "stop"})
            self.assertEqual(ws.receive_json()["observation"]["capture_status"], "ended")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/frame").status_code, 410)
        stopped = self.client.post(f"/screen-sessions/{self.sid}/stop", headers=self.headers).json()
        self.assertEqual(stopped["received_frame_count"], 1)

    def test_ownership_and_cross_origin(self):
        outsider = TestClient(self.app)
        outsider.get("/")
        self.assertEqual(outsider.get(f"/screen-sessions/{self.sid}/observation").status_code, 404)
        self.assertEqual(outsider.get(f"/screen-sessions/{self.sid}/frame").status_code, 404)
        self.assertEqual(self.client.post("/screen-sessions", headers={"origin": "https://foreign.example"}).status_code, 403)
        outsider.close()

    def test_conflicting_duplicate_rejected(self):
        with self.connect() as ws:
            self.start(ws)
            self.assertEqual(self.send(ws)["type"], "ack")
            changed = dict(self.meta, captured_elapsed_ms=20)
            self.assertEqual(self.send(ws, changed)["type"], "error")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["received_frame_count"], 1)

    def test_identical_duplicate_is_idempotent(self):
        with self.connect() as ws:
            self.start(ws)
            self.send(ws)
            ack = self.send(ws)
            self.assertTrue(ack["duplicate"])
            self.assertEqual(ack["observation"]["received_frame_count"], 1)

    def test_pause_rejects_frames_and_resume_works(self):
        with self.connect() as ws:
            self.start(ws)
            ws.send_json({"type": "pause"})
            self.assertEqual(ws.receive_json()["observation"]["capture_status"], "paused")
            ws.send_json({"type": "heartbeat"})
            self.assertEqual(ws.receive_json()["type"], "heartbeat")
            ws.send_json({"type": "resume"})
            self.assertEqual(ws.receive_json()["observation"]["capture_status"], "sharing")
            self.assertEqual(self.send(ws)["type"], "ack")

    def test_invalid_image_does_not_become_latest(self):
        with self.connect() as ws:
            self.start(ws)
            self.assertEqual(self.send(ws, dict(self.meta, byte_count=5), b"hello")["type"], "error")
        snapshot = self.client.get(f"/screen-sessions/{self.sid}/observation").json()
        self.assertEqual(snapshot["received_frame_count"], 0)
        self.assertIsNone(snapshot["observation"])

    def test_dimension_mismatch_rejected(self):
        with self.connect() as ws:
            self.start(ws)
            bad = dict(self.meta, width=160, height=90)
            self.assertEqual(self.send(ws, bad)["type"], "error")

    def test_non_integer_metadata_rejected(self):
        with self.connect() as ws:
            self.start(ws)
            ws.send_json(dict(self.meta, sequence=True))
            self.assertEqual(ws.receive_json()["type"], "error")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["received_frame_count"], 0)

    def test_frame_rate_is_bounded(self):
        with self.connect() as ws:
            self.start(ws)
            self.send(ws)
            self.assertEqual(self.send(ws, dict(self.meta, sequence=2, captured_elapsed_ms=20))["type"], "skipped")

    def test_rest_stop_blocks_late_frame(self):
        with self.connect() as ws:
            self.start(ws)
            self.client.post(f"/screen-sessions/{self.sid}/stop", headers=self.headers)
            ws.send_json(self.meta)
            self.assertEqual(ws.receive_json()["type"], "error")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["received_frame_count"], 0)

    def test_disconnect_drops_pixels_but_keeps_metadata(self):
        with self.connect() as ws:
            self.start(ws)
            self.send(ws)
        observation = self.client.get(f"/screen-sessions/{self.sid}/observation").json()
        self.assertEqual(observation["capture_status"], "disconnected")
        self.assertFalse(observation["evidence"]["latest_image_available"])
        self.assertEqual(observation["received_frame_count"], 1)
        # Only SQLite metadata exists; no raw frame files are written.
        self.assertTrue(all(p.name.startswith(('sessions.sqlite', 'labs.sqlite')) for p in Path(self.directory.name).iterdir()))

    def test_restart_requires_fresh_capture(self):
        with self.connect() as ws:
            self.start(ws)
            self.send(ws)
        self.app.state.store.set_status(self.sid, "sharing", "fixture_simulated_crash")
        restarted = create_app(Path(self.directory.name))
        owner = self.client.cookies[COOKIE]
        row = restarted.state.store.session(self.sid, owner)
        self.assertEqual(row["status"], "disconnected")
        self.assertEqual(json.loads(row["latest"])["sequence"], 1)
        restarted.state.store.db.close()
        restarted.state.lab.store.db.close()

    def test_reconnect_cannot_move_capture_clock_backwards(self):
        with self.connect() as ws:
            self.start(ws)
            self.send(ws)
        with self.connect() as ws:
            self.start(ws)
            self.assertEqual(self.send(ws, dict(self.meta, sequence=2, captured_elapsed_ms=1))["type"], "error")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["received_frame_count"], 1)

    def test_paused_session_rejects_frame_metadata(self):
        with self.connect() as ws:
            self.start(ws)
            ws.send_json({"type": "pause"})
            ws.receive_json()
            ws.send_json(self.meta)
            self.assertEqual(ws.receive_json()["type"], "error")
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["received_frame_count"], 0)

    def test_duration_does_not_expire_session_and_oversized_frames_remain_rejected(self):
        with self.connect() as ws:
            self.start(ws)
            ws.send_json(dict(self.meta, byte_count=1000001))
            self.assertEqual(ws.receive_json()["type"], "error")
        self.app.state.store.db.execute("UPDATE sessions SET created=created-1801 WHERE id=?", (self.sid,))
        self.app.state.store.db.commit()
        self.assertEqual(self.client.get(f"/screen-sessions/{self.sid}/observation").json()["capture_status"], "disconnected")
        with self.connect() as ws:
            self.start(ws)
            ws.send_json(dict(self.meta, captured_elapsed_ms=1_900_000))
            ws.send_bytes(self.image)
            self.assertEqual(ws.receive_json()["type"], "ack")

    def test_websocket_requires_same_origin_and_single_producer(self):
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect(f"/screen-sessions/{self.sid}/stream", headers={"origin": "https://foreign.example"}):
                pass
        with self.connect() as ws:
            self.start(ws)
            with self.assertRaises(WebSocketDisconnect):
                with self.connect():
                    pass


if __name__ == "__main__":
    unittest.main()
