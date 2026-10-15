CREATE TABLE IF NOT EXISTS writing_delivery_acks (
 session_id TEXT NOT NULL,
 owner TEXT NOT NULL,
 packet_id TEXT NOT NULL,
 ack_json TEXT NOT NULL,
 PRIMARY KEY(session_id, packet_id),
 FOREIGN KEY(session_id) REFERENCES lab_sessions(id) ON DELETE CASCADE
);
