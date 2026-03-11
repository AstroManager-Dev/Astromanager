CREATE TABLE IF NOT EXISTS target_final (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,

  canonical_name TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  slug TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',

  final_name TEXT NOT NULL DEFAULT '',
  final_name_source TEXT NOT NULL DEFAULT '',

  final_objtype TEXT NOT NULL DEFAULT '',
  final_objtype_source TEXT NOT NULL DEFAULT '',

  final_ra_deg REAL,
  final_dec_deg REAL,
  final_coord_source TEXT NOT NULL DEFAULT '',

  final_distance_value REAL,
  final_distance_unit TEXT NOT NULL DEFAULT '',
  distance_ly REAL,
  distance_source TEXT NOT NULL DEFAULT '',
  distance_ref TEXT NOT NULL DEFAULT '',

  mag_value REAL,
  mag_band TEXT NOT NULL DEFAULT '',
  mag_source TEXT NOT NULL DEFAULT '',

  constellation_code TEXT NOT NULL DEFAULT '',
  constellation_name TEXT NOT NULL DEFAULT '',
  constellation_source TEXT NOT NULL DEFAULT '',

  identity_method TEXT NOT NULL DEFAULT '',
  identity_confidence REAL,
  coord_match_sep_arcsec REAL,
  angular_size_arcmin REAL,

  final_source_summary TEXT NOT NULL DEFAULT '',
  merge_status TEXT NOT NULL DEFAULT 'pending',
  merge_notes TEXT NOT NULL DEFAULT '',

  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_target_final_target_id
  ON target_final(target_id);

CREATE INDEX IF NOT EXISTS idx_target_final_name
  ON target_final(final_name);

CREATE INDEX IF NOT EXISTS idx_target_final_category
  ON target_final(category);

CREATE INDEX IF NOT EXISTS idx_target_final_constellation_code
  ON target_final(constellation_code);

CREATE INDEX IF NOT EXISTS idx_target_final_merge_status
  ON target_final(merge_status);
