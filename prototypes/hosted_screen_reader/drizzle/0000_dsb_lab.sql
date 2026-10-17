CREATE TABLE lab_sessions (
 id TEXT PRIMARY KEY,
 owner TEXT NOT NULL,
 revision INTEGER NOT NULL,
 mutation_id TEXT NOT NULL,
 state_json TEXT NOT NULL,
 updated_at INTEGER NOT NULL,
 capture_heartbeat INTEGER NOT NULL DEFAULT 0,
 last_frame_id TEXT
);
--> statement-breakpoint
CREATE INDEX lab_sessions_owner_time ON lab_sessions(owner, updated_at);
--> statement-breakpoint
CREATE TABLE lab_events (
 session_id TEXT NOT NULL,
 event_id TEXT NOT NULL,
 sequence INTEGER NOT NULL,
 event_json TEXT NOT NULL,
 PRIMARY KEY(session_id,event_id),
 UNIQUE(session_id,sequence),
 FOREIGN KEY(session_id) REFERENCES lab_sessions(id)
);
--> statement-breakpoint
CREATE TABLE lab_images (
 session_id TEXT PRIMARY KEY,
 owner TEXT NOT NULL,
 frame_id TEXT NOT NULL,
 observation_id TEXT NOT NULL,
 received_at INTEGER NOT NULL,
 jpeg BLOB NOT NULL,
 FOREIGN KEY(session_id) REFERENCES lab_sessions(id)
);
