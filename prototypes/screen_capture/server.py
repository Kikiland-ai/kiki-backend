"""Small, single-instance FastAPI frame receiver with durable metadata only."""

import asyncio
import hashlib
import io
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from contracts.screen_capture import FrameEnvelope
from prototypes.lab_tracking.api import lab_router
from prototypes.lab_tracking.service import LabService
from prototypes.screen_capture.cloud_access import SiteProxyGuard

STATIC = Path(__file__).parent / "static"
COOKIE = "kiki_capture_owner"
SESSION_SECONDS = None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def same_origin(origin, host):
    if not origin:
        return False
    parsed = urlsplit(origin)
    return parsed.scheme in ("http", "https") and parsed.netloc == host


def validate_image(payload, meta):
    if len(payload) != meta.byte_count:
        raise ValueError("Image byte count does not match its envelope")
    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != "JPEG" or image.size != (meta.width, meta.height):
                raise ValueError("Image format or dimensions do not match its envelope")
            image.verify()
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Invalid JPEG image") from exc


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "sessions.sqlite", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, created REAL NOT NULL,
                status TEXT NOT NULL, frame_count INTEGER NOT NULL DEFAULT 0,
                latest_sequence INTEGER NOT NULL DEFAULT 0, latest TEXT,
                event_sequence INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS events (
                session_id TEXT NOT NULL, sequence INTEGER NOT NULL, body TEXT NOT NULL,
                PRIMARY KEY(session_id, sequence)
            );
        """)
        # A restart never establishes that browser sharing has continued.
        for row in self.db.execute("SELECT id FROM sessions WHERE status IN ('sharing','paused')").fetchall():
            self.set_status(row["id"], "disconnected", "server_restarted")

    def session(self, session_id, owner):
        row = self.db.execute("SELECT * FROM sessions WHERE id=? AND owner=?", (session_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        return row

    def event(self, session_id, kind, data=None):
        row = self.db.execute("SELECT event_sequence FROM sessions WHERE id=?", (session_id,)).fetchone()
        seq = row[0] + 1
        body = {"event_id": f"{session_id}:{seq}", "sequence": seq, "type": kind,
                "server_time": utc_now(), "data": data or {}}
        self.db.execute("INSERT INTO events VALUES (?,?,?)", (session_id, seq, json.dumps(body)))
        self.db.execute("UPDATE sessions SET event_sequence=? WHERE id=?", (seq, session_id))
        return body

    def create(self, owner):
        session_id = secrets.token_hex(16)
        with self.db:
            self.db.execute("INSERT INTO sessions(id,owner,created,status) VALUES(?,?,?,?)",
                            (session_id, owner, time.time(), "awaiting_share"))
            self.event(session_id, "session_created")
        return session_id

    def set_status(self, session_id, status, reason):
        with self.db:
            self.db.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))
            return self.event(session_id, reason, {"status": status})

    def frame(self, session_id, metadata):
        with self.db:
            event = self.event(session_id, "frame_received", metadata)
            metadata["event_id"] = event["event_id"]
            self.db.execute("UPDATE sessions SET latest=?,latest_sequence=?,frame_count=frame_count+1 WHERE id=?",
                            (json.dumps(metadata), metadata["sequence"], session_id))
        return event


def create_app(data_dir=Path("work/screen-capture"), *, analyzer=None, clock=time.time, proxy_secret=None):
    proxy_secret = os.environ.get("KIKI_PROXY_SECRET", "") if proxy_secret is None else proxy_secret
    if (proxy_secret and len(proxy_secret) < 32) or (os.environ.get("KIKI_REQUIRE_PROXY") == "1" and not proxy_secret):
        raise RuntimeError("Cloud mode requires a server-side proxy secret of at least 32 characters")
    store = Store(Path(data_dir))
    app = FastAPI(title="Kiki screen capture receiver")
    app.state.store = store
    latest_images = {}
    producers = set()
    last_admission = {}

    def owner_of(request):
        owner = request.headers.get("x-kiki-owner") if proxy_secret else request.cookies.get(COOKIE)
        if not owner:
            raise HTTPException(401, "Open the capture page first")
        return owner

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    def owned(request, session_id):
        return store.session(session_id, owner_of(request))

    def mutation_origin(request):
        if not same_origin(request.headers.get("origin"), request.headers.get("host")):
            raise HTTPException(403, "Same-origin request required")

    def expire(row):
        # A live session ends explicitly, never because its creation time is old.
        return row

    def capture_access(session_id, owner):
        if not session_id:
            raise HTTPException(409, "Attach a screen share to this lab first")
        row = expire(store.session(session_id, owner))
        return {"status": row["status"], "frame": json.loads(row["latest"]) if row["latest"] else None,
                "pixels": latest_images.get(session_id)}

    lab = LabService(Path(data_dir), capture_access, analyzer=analyzer, clock=clock)
    app.state.lab = lab
    app.include_router(lab_router(lab, owner_of, mutation_origin))

    def snapshot(row):
        row = expire(row)
        meta = json.loads(row["latest"]) if row["latest"] else None
        age = int((time.time() - meta["server_received_unix"]) * 1000) if meta else None
        return {"schema": "screen-receiver/v1", "session_id": row["id"], "capture_epoch": 1,
                "capture_status": row["status"], "received_frame_count": row["frame_count"],
                "observation": {"mode": "frame_receipt", "analysis_status": "not_enabled",
                                "summary": None, "latest_frame": meta} if meta else None,
                "freshness": {"received_age_ms": age, "stale": age is None or age > 10000},
                "evidence": {"latest_image_available": row["id"] in latest_images,
                             "retention": "latest_image_in_memory_only"},
                "last_event_sequence": row["event_sequence"]}

    @app.get("/")
    async def page(request: Request):
        response = FileResponse(STATIC / "index.html")
        if proxy_secret:
            return response
        owner = request.cookies.get(COOKIE, "")
        if len(owner) != 64 or any(c not in "0123456789abcdef" for c in owner):
            response.set_cookie(COOKIE, secrets.token_hex(32), httponly=True, samesite="strict",
                                secure=request.url.scheme == "https", max_age=86400)
        return response

    @app.get("/static/{name}")
    async def asset(name: str):
        if name not in ("capture.js", "style.css", "lab.js", "lab-cadence.js"):
            raise HTTPException(404)
        return FileResponse(STATIC / name)

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "frame_receipt_and_reviewed_lab", "sample_hz": 0.5,
                "analysis": {"provider": "gemini", "configured": lab.analyzer.configured,
                             "model": getattr(lab.analyzer, "model", "injected_test_adapter"),
                             "minimum_interval_seconds": 3, "checks_per_lab": None,
                             "key_count": len(getattr(getattr(lab.analyzer, "provider", None), "keys", [])),
                             "configuration_valid": not getattr(getattr(lab.analyzer, "provider", None), "invalid", False),
                             "rotation_enabled": len(getattr(getattr(lab.analyzer, "provider", None), "keys", [])) > 1},
                "backend": "python_fastapi", "lab_storage": "sqlite_metadata",
                "image_storage": "latest_pixels_in_memory_only"}

    @app.post("/screen-sessions", status_code=201)
    async def new_session(request: Request):
        mutation_origin(request)
        owner = owner_of(request)
        session_id = store.create(owner)
        return {"session_id": session_id, "stream_path": f"/screen-sessions/{session_id}/stream",
                "sample_interval_ms": 2000, "max_frame_bytes": 1000000, "session_limit_seconds": SESSION_SECONDS}

    @app.get("/screen-sessions/{session_id}/observation")
    async def observation(session_id: str, request: Request):
        return snapshot(owned(request, session_id))

    @app.get("/screen-sessions/{session_id}/frame")
    async def image(session_id: str, request: Request):
        row = expire(owned(request, session_id))
        data = latest_images.get(session_id)
        if data is None:
            raise HTTPException(410, "Latest image is unavailable; only frame metadata is persisted")
        return Response(data, media_type="image/jpeg", headers={"X-Frame-Sequence": str(row["latest_sequence"])})

    @app.get("/screen-sessions/{session_id}/events")
    async def events(session_id: str, request: Request, after: int = 0, limit: int = 100):
        owned(request, session_id)
        if after < 0 or not 1 <= limit <= 100:
            raise HTTPException(422, "Invalid event cursor or limit")
        rows = store.db.execute("SELECT body FROM events WHERE session_id=? AND sequence>? ORDER BY sequence LIMIT ?",
                                (session_id, after, limit)).fetchall()
        items = [json.loads(row[0]) for row in rows]
        return {"events": items, "next_cursor": items[-1]["sequence"] if items else after}

    @app.post("/screen-sessions/{session_id}/stop")
    async def stop(session_id: str, request: Request):
        mutation_origin(request)
        row = owned(request, session_id)
        if row["status"] not in ("ended", "expired"):
            store.set_status(session_id, "ended", "capture_stopped")
        latest_images.pop(session_id, None)
        lab.capture_changed(session_id, "ended")
        return snapshot(store.session(session_id, row["owner"]))

    @app.websocket("/screen-sessions/{session_id}/stream")
    async def stream(ws: WebSocket, session_id: str):
        if not same_origin(ws.headers.get("origin"), ws.headers.get("host")):
            await ws.close(code=1008)
            return
        try:
            row = expire(store.session(session_id, owner_of(ws)))
        except HTTPException:
            await ws.close(code=1008)
            return
        if session_id in producers or row["status"] in ("ended", "expired"):
            await ws.close(code=1008)
            return
        producers.add(session_id)
        await ws.accept()
        last_elapsed = -1
        try:
            await ws.send_json({"type": "connected", "observation": snapshot(row)})
            while True:
                message = await asyncio.wait_for(ws.receive(), timeout=20)
                if message["type"] == "websocket.disconnect":
                    break
                text = message.get("text")
                if text is None or len(text.encode()) > 4096:
                    raise ValueError("Expected bounded frame metadata")
                body = json.loads(text)
                if not isinstance(body, dict):
                    raise ValueError("Expected JSON object")
                row = expire(store.session(session_id, row["owner"]))
                if row["status"] in ("ended", "expired"):
                    raise ValueError("Session has ended")
                kind = body.get("type")
                if kind == "heartbeat":
                    await ws.send_json({"type": "heartbeat", "observation": snapshot(row)})
                    continue
                if kind in ("capture_started", "pause", "resume", "stop"):
                    desired = {"capture_started": "sharing", "pause": "paused", "resume": "sharing", "stop": "ended"}[kind]
                    store.set_status(session_id, desired, kind)
                    lab.capture_changed(session_id, desired)
                    if kind == "stop":
                        latest_images.pop(session_id, None)
                    await ws.send_json({"type": "status", "observation": snapshot(store.session(session_id, row["owner"]))})
                    if kind == "stop":
                        break
                    continue
                meta = FrameEnvelope.model_validate(body)
                if row["status"] != "sharing":
                    raise ValueError("Capture must be active before sending frames")
                binary = await asyncio.wait_for(ws.receive(), timeout=5)
                payload = binary.get("bytes")
                if payload is None or len(payload) > 1000000:
                    raise ValueError("Expected image bytes, at most 1 MB")
                await asyncio.to_thread(validate_image, payload, meta)
                # Validate again after asynchronous decode: stop may have occurred meanwhile.
                current = expire(store.session(session_id, row["owner"]))
                if current["status"] != "sharing":
                    raise ValueError("Capture is no longer active")
                digest = hashlib.sha256(payload).hexdigest()
                previous = json.loads(current["latest"]) if current["latest"] else None
                if meta.sequence == current["latest_sequence"] and previous and digest == previous["sha256"]:
                    if any(previous.get(key) != value for key, value in meta.model_dump(exclude={"type"}).items()):
                        raise ValueError("Duplicate frame envelope conflicts")
                    await ws.send_json({"type": "ack", "duplicate": True, "observation": snapshot(current)})
                    continue
                previous_elapsed = previous["captured_elapsed_ms"] if previous else -1
                if meta.sequence <= current["latest_sequence"] or meta.captured_elapsed_ms < max(last_elapsed, previous_elapsed):
                    raise ValueError("Frame order must increase")
                if previous and meta.view_revision < previous.get("view_revision", 1):
                    raise ValueError("View revision cannot move backwards")
                if time.monotonic() - last_admission.get(session_id, -100) < 1.8:
                    await ws.send_json({"type": "skipped", "reason": "sampling_limit"})
                    continue
                previous_sequence = current["latest_sequence"]
                metadata = meta.model_dump(exclude={"type"})
                metadata.update({"frame_id": f"{session_id}:1:{meta.sequence}", "sha256": digest,
                                 "server_received_at": utc_now(), "server_received_unix": time.time(),
                                 "skipped_sequences": max(0, meta.sequence - previous_sequence - 1)})
                store.frame(session_id, metadata)
                latest_images[session_id] = payload
                lab.capture_changed(session_id, "sharing", meta.view_revision)
                last_elapsed = meta.captured_elapsed_ms
                last_admission[session_id] = time.monotonic()
                await ws.send_json({"type": "ack", "observation": snapshot(store.session(session_id, row["owner"]))})
        except WebSocketDisconnect:
            pass
        except (ValueError, ValidationError, asyncio.TimeoutError):
            # Do not reflect arbitrary client content or frame data into errors/logs.
            store.event(session_id, "protocol_rejected")
            store.db.commit()
            try:
                await ws.send_json({"type": "error", "message": "Frame protocol rejected or timed out; start a new share."})
            except (WebSocketDisconnect, RuntimeError):
                pass
        finally:
            producers.discard(session_id)
            row = store.session(session_id, row["owner"])
            if row["status"] not in ("ended", "expired"):
                store.set_status(session_id, "disconnected", "capture_disconnected")
                lab.capture_changed(session_id, "disconnected")
            latest_images.pop(session_id, None)
            last_admission.pop(session_id, None)
            try:
                await ws.close()
            except RuntimeError:
                pass

    if proxy_secret:
        app.add_middleware(SiteProxyGuard, secret=proxy_secret)
    return app
