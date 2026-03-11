PRAGMA foreign_keys=OFF;
BEGIN;

CREATE TABLE IF NOT EXISTS target_sesame_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  resolver_name TEXT,
  sesame_oid TEXT,
  sesame_oname TEXT,
  sesame_otype TEXT,
  sesame_mtype TEXT,
  ra_deg REAL,
  dec_deg REAL,
  coord_text TEXT,
  coord_ref TEXT,
  vel_value REAL,
  vel_error REAL,
  vel_quality TEXT,
  vel_ref TEXT,
  nrefs INTEGER,
  status TEXT,
  source TEXT,
  error_message TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_vizier_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  catalog_source TEXT,
  main_id TEXT,
  preferred_name TEXT,
  aliases TEXT,
  object_type TEXT,
  object_type_label TEXT,
  ra_deg REAL,
  dec_deg REAL,
  ra_text TEXT,
  dec_text TEXT,
  magnitude_value REAL,
  magnitude_band TEXT,
  distance_value REAL,
  distance_unit TEXT,
  identifier_count INTEGER,
  status TEXT,
  source TEXT,
  error_message TEXT,
  request_url TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_ssodnet_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  resolver_id TEXT,
  object_type TEXT,
  object_class TEXT,
  display_name TEXT,
  number_text TEXT,
  title TEXT,
  aliases TEXT,
  parent_name TEXT,
  system_name TEXT,
  has_ephemeris INTEGER NOT NULL DEFAULT 0,
  has_physical_ephemeris INTEGER NOT NULL DEFAULT 0,
  has_physical_models INTEGER NOT NULL DEFAULT 0,
  ra_deg REAL,
  dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_target_sesame_resolve_target_id
  ON target_sesame_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_sesame_resolve_status
  ON target_sesame_resolve(status);

CREATE INDEX IF NOT EXISTS idx_target_vizier_resolve_target_id
  ON target_vizier_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_vizier_resolve_status
  ON target_vizier_resolve(status);

CREATE INDEX IF NOT EXISTS idx_target_ssodnet_resolve_target_id
  ON target_ssodnet_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_ssodnet_resolve_status
  ON target_ssodnet_resolve(status);

COMMIT;
PRAGMA foreign_keys=ON;
