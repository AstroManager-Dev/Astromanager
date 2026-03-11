PRAGMA foreign_keys=OFF;
BEGIN;

CREATE TABLE IF NOT EXISTS session_platesolve_resolve (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL UNIQUE,
  session_key TEXT,
  target TEXT,
  platesolve_status TEXT,
  platesolve_attempts INTEGER,
  platesolve_last_at TEXT,
  platesolve_reference_path TEXT,
  solve_ra_deg REAL,
  solve_dec_deg REAL,
  solve_fov_x_deg REAL,
  solve_fov_y_deg REAL,
  solve_rotation_deg REAL,
  footprint_radius_deg REAL,
  corner_ul_ra_deg REAL,
  corner_ul_dec_deg REAL,
  corner_ur_ra_deg REAL,
  corner_ur_dec_deg REAL,
  corner_lr_ra_deg REAL,
  corner_lr_dec_deg REAL,
  corner_ll_ra_deg REAL,
  corner_ll_dec_deg REAL,
  solve_engine TEXT,
  solve_message TEXT,
  solve_pass TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS session_target_resolve (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL UNIQUE,
  session_key TEXT,
  target_raw TEXT,
  target_final TEXT,
  target_final_source TEXT,
  target_strategy TEXT,
  field_object_count INTEGER,
  requested_target_found INTEGER,
  target_conflict_flag INTEGER,
  target_conflict_note TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS session_target_resolve_item (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  target_id INTEGER,
  target_name TEXT,
  object_type TEXT,
  source TEXT,
  is_requested_target INTEGER NOT NULL DEFAULT 0,
  is_primary INTEGER NOT NULL DEFAULT 0,
  is_major INTEGER NOT NULL DEFAULT 0,
  priority_rank INTEGER,
  score REAL,
  distance_to_center_deg REAL,
  in_frame_fraction REAL,
  angular_size_arcmin REAL,
  ra_deg REAL,
  dec_deg REAL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_session_target_resolve_item_session_id
  ON session_target_resolve_item(session_id);

CREATE INDEX IF NOT EXISTS idx_session_target_resolve_item_target_id
  ON session_target_resolve_item(target_id);

CREATE TABLE IF NOT EXISTS target_base_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  display_name TEXT,
  category TEXT,
  ra_deg REAL,
  dec_deg REAL,
  coord_text TEXT,
  coord_ref TEXT,
  status TEXT,
  source TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_wikidata_name_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  wikidata_id TEXT,
  label_de TEXT,
  label_en TEXT,
  aliases_de TEXT,
  aliases_en TEXT,
  wiki_de_title TEXT,
  wiki_en_title TEXT,
  resolved_name TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_wikidata_meta_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  wikidata_id TEXT,
  object_type TEXT,
  object_type_label_de TEXT,
  object_type_label_en TEXT,
  mag_value REAL,
  mag_band TEXT,
  distance_value REAL,
  distance_unit TEXT,
  distance_unit_label_de TEXT,
  distance_unit_label_en TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_simbad_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  simbad_main_id TEXT,
  simbad_otype TEXT,
  simbad_ra_deg REAL,
  simbad_dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_ned_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  ned_objtype TEXT,
  ned_ra_deg REAL,
  ned_dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_constellation_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  constellation TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS target_nasa_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  nasa_title TEXT,
  nasa_page_url TEXT,
  nasa_image_url TEXT,
  nasa_thumb_url TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_target_base_resolve_target_id
  ON target_base_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_wikidata_name_resolve_target_id
  ON target_wikidata_name_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_wikidata_meta_resolve_target_id
  ON target_wikidata_meta_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_simbad_resolve_target_id
  ON target_simbad_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_ned_resolve_target_id
  ON target_ned_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_constellation_resolve_target_id
  ON target_constellation_resolve(target_id);

CREATE INDEX IF NOT EXISTS idx_target_nasa_resolve_target_id
  ON target_nasa_resolve(target_id);

COMMIT;
PRAGMA foreign_keys=ON;
