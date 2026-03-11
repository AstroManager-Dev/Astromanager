CREATE TABLE IF NOT EXISTS target_skyview_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  survey TEXT NOT NULL DEFAULT 'DSS2 Color',
  position_source TEXT NOT NULL DEFAULT '',
  ra_deg REAL,
  dec_deg REAL,
  image_url TEXT NOT NULL DEFAULT '',
  fits_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_target_skyview_resolve_status
  ON target_skyview_resolve(status);

CREATE TABLE IF NOT EXISTS target_irsa_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  position_source TEXT NOT NULL DEFAULT '',
  ra_deg REAL,
  dec_deg REAL,
  viewer_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_target_irsa_resolve_status
  ON target_irsa_resolve(status);
