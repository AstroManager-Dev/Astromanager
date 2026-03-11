PRAGMA foreign_keys=OFF;
BEGIN;

CREATE TABLE IF NOT EXISTS external_source_state (
  id INTEGER PRIMARY KEY,
  source_key TEXT NOT NULL UNIQUE,
  source_url TEXT NOT NULL DEFAULT '',
  local_path TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  last_checked_at TEXT,
  last_downloaded_at TEXT,
  expires_at TEXT,
  etag TEXT NOT NULL DEFAULT '',
  last_modified TEXT NOT NULL DEFAULT '',
  error_message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_external_source_state_source_key
  ON external_source_state(source_key);

COMMIT;
PRAGMA foreign_keys=ON;
