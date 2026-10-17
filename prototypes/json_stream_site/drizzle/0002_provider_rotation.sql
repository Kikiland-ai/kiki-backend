CREATE TABLE IF NOT EXISTS provider_rotation (
 router_id TEXT PRIMARY KEY,
 last_key TEXT,
 failed_keys TEXT NOT NULL DEFAULT '[]',
 retry_at INTEGER NOT NULL DEFAULT 0,
 lease_owner TEXT,
 lease_until INTEGER NOT NULL DEFAULT 0,
 last_error TEXT
);
