CREATE TABLE IF NOT EXISTS target_name_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL,
  canonical_name TEXT,
  slug TEXT,
  resolved_name TEXT,
  source TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_target_name_resolve_target_id
  ON target_name_resolve(target_id);
