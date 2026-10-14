CREATE TABLE IF NOT EXISTS provider_cooldowns (
 pool_id TEXT PRIMARY KEY,
 retry_at INTEGER NOT NULL,
 failures INTEGER NOT NULL
);
