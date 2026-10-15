CREATE TABLE IF NOT EXISTS guidance_streams (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, session_id TEXT NOT NULL, capture_id TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1, sequence INTEGER NOT NULL DEFAULT 0,
 fence_revision INTEGER NOT NULL DEFAULT 0, publication_id TEXT, context_json TEXT NOT NULL,
 challenge TEXT NOT NULL, identity_json TEXT NOT NULL, created_at INTEGER NOT NULL,
 FOREIGN KEY(session_id) REFERENCES lab_sessions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS guidance_stream_owner ON guidance_streams(owner,session_id,active);
CREATE TABLE IF NOT EXISTS guidance_outbox (
 stream_id TEXT NOT NULL, sequence INTEGER NOT NULL, publication_id TEXT NOT NULL UNIQUE,
 message_json TEXT NOT NULL, created_at INTEGER NOT NULL,
 PRIMARY KEY(stream_id,sequence), FOREIGN KEY(stream_id) REFERENCES guidance_streams(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS guidance_acks (
 ack_id TEXT PRIMARY KEY, owner TEXT NOT NULL, stream_id TEXT NOT NULL, sequence INTEGER NOT NULL,
 packet_id TEXT, received_at INTEGER NOT NULL, ack_json TEXT NOT NULL, timing_json TEXT NOT NULL,
 UNIQUE(stream_id,sequence), FOREIGN KEY(stream_id,sequence) REFERENCES guidance_outbox(stream_id,sequence) ON DELETE CASCADE
);
