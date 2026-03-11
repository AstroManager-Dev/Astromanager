CREATE TABLE job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_name TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT,
  source TEXT NOT NULL DEFAULT 'unknown',
  note TEXT DEFAULT '',
  stdout_log TEXT DEFAULT '',
  stderr_log TEXT DEFAULT ''
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE app_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE device_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_key TEXT NOT NULL UNIQUE,
  vendor TEXT NOT NULL,
  model TEXT NOT NULL,
  family TEXT NOT NULL DEFAULT 'smart_telescope',
  protocol TEXT NOT NULL DEFAULT '',
  root_pattern TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  session_key TEXT NOT NULL UNIQUE,
  session_type TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'unknown',
  raw_session_path TEXT NOT NULL UNIQUE,
  target TEXT NOT NULL,
  filter_set TEXT NOT NULL DEFAULT 'unknown',
  exp REAL,
  gain INTEGER,
  binning INTEGER,
  session_datetime TEXT NOT NULL,
  source_origin TEXT NOT NULL DEFAULT 'dwarf_sync',
  status TEXT NOT NULL DEFAULT 'indexed',
  frame_count INTEGER NOT NULL DEFAULT 0,
  total_bytes INTEGER NOT NULL DEFAULT 0,
  temp_min REAL,
  temp_max REAL,
  temp_avg REAL,
  has_dwarf_stack INTEGER NOT NULL DEFAULT 0,
  has_dwarf_preview INTEGER NOT NULL DEFAULT 0,
  has_dwarf_metadata INTEGER NOT NULL DEFAULT 0,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')), target_id INTEGER, capture_profile_id INTEGER,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE raw_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  source_domain TEXT NOT NULL,
  source_subtype TEXT NOT NULL,
  abs_path TEXT NOT NULL UNIQUE,
  rel_path TEXT NOT NULL,
  parent_dir TEXT NOT NULL,
  file_name TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  mtime_epoch INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  session_key TEXT DEFAULT '',
  filter_set TEXT NOT NULL DEFAULT 'unknown',
  file_status TEXT NOT NULL DEFAULT 'ok',
  file_status_note TEXT DEFAULT '',
  derivative_kind TEXT NOT NULL DEFAULT '',
  is_session_input INTEGER NOT NULL DEFAULT 0,
  is_dwarf_generated INTEGER NOT NULL DEFAULT 0,
  header_object TEXT NOT NULL DEFAULT '',
  header_ra TEXT NOT NULL DEFAULT '',
  header_dec TEXT NOT NULL DEFAULT '',
  header_exptime REAL,
  header_gain REAL,
  header_filter TEXT NOT NULL DEFAULT '',
  header_date_obs TEXT NOT NULL DEFAULT '',
  header_bayerpat TEXT NOT NULL DEFAULT '',
  header_xbayroff INTEGER,
  header_ybayroff INTEGER,
  is_color_sensor INTEGER NOT NULL DEFAULT 0,
  debayer_required INTEGER NOT NULL DEFAULT 0,
  exp REAL,
  gain INTEGER,
  temp_c REAL,
  binning INTEGER,
  camera TEXT DEFAULT '',
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  is_current INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE calibration_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  asset_type TEXT NOT NULL,
  asset_origin TEXT NOT NULL,
  camera TEXT NOT NULL DEFAULT '',
  abs_path TEXT NOT NULL UNIQUE,
  rel_path TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  mtime_epoch INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  exp REAL,
  gain INTEGER,
  binning INTEGER,
  temp_c REAL,
  stack_count INTEGER,
  ir_index INTEGER,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  is_current INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  , ra_deg REAL, dec_deg REAL, coord_text TEXT NOT NULL DEFAULT '', coord_source TEXT NOT NULL DEFAULT '', coord_ref TEXT NOT NULL DEFAULT '', coord_status TEXT NOT NULL DEFAULT 'pending', name_status TEXT NOT NULL DEFAULT 'pending', name_source TEXT NOT NULL DEFAULT '', name_resolved_at TEXT, wikidata_id TEXT NOT NULL DEFAULT '', label_de TEXT NOT NULL DEFAULT '', label_en TEXT NOT NULL DEFAULT '', aliases_de TEXT NOT NULL DEFAULT '', aliases_en TEXT NOT NULL DEFAULT '', wiki_de_title TEXT NOT NULL DEFAULT '', wiki_en_title TEXT NOT NULL DEFAULT '', object_type TEXT NOT NULL DEFAULT '', mag_value REAL, mag_band TEXT NOT NULL DEFAULT '', distance_value REAL, distance_unit TEXT NOT NULL DEFAULT '', meta_status TEXT NOT NULL DEFAULT 'pending', meta_source TEXT NOT NULL DEFAULT '', meta_resolved_at TEXT, object_type_label_de TEXT NOT NULL DEFAULT '', object_type_label_en TEXT NOT NULL DEFAULT '', distance_unit_label_de TEXT NOT NULL DEFAULT '', distance_unit_label_en TEXT NOT NULL DEFAULT '', ned_preferred_name TEXT NOT NULL DEFAULT '', ned_objtype TEXT NOT NULL DEFAULT '', ned_ra_deg REAL, ned_dec_deg REAL, ned_redshift REAL, ned_status TEXT NOT NULL DEFAULT 'pending', ned_source TEXT NOT NULL DEFAULT '', ned_resolved_at TEXT, simbad_main_id TEXT NOT NULL DEFAULT '', simbad_otype TEXT NOT NULL DEFAULT '', simbad_ra_deg REAL, simbad_dec_deg REAL, simbad_status TEXT NOT NULL DEFAULT 'pending', simbad_source TEXT NOT NULL DEFAULT '', simbad_resolved_at TEXT, final_name TEXT NOT NULL DEFAULT '', final_objtype TEXT NOT NULL DEFAULT '', final_ra_deg REAL, final_dec_deg REAL, final_distance_value REAL, final_distance_unit TEXT NOT NULL DEFAULT '', final_source_summary TEXT NOT NULL DEFAULT '', nasa_image_url TEXT NOT NULL DEFAULT '', nasa_thumb_url TEXT NOT NULL DEFAULT '', nasa_title TEXT NOT NULL DEFAULT '', nasa_nasa_id TEXT NOT NULL DEFAULT '', nasa_status TEXT NOT NULL DEFAULT 'pending', nasa_source TEXT NOT NULL DEFAULT '', nasa_resolved_at TEXT, nasa_page_url TEXT NOT NULL DEFAULT '', nasa_asset_manifest_url TEXT NOT NULL DEFAULT '', distance_source TEXT NOT NULL DEFAULT '', distance_ref TEXT NOT NULL DEFAULT '', distance_ly REAL, identity_method TEXT NOT NULL DEFAULT '', identity_confidence REAL, coord_match_sep_arcsec REAL, constellation TEXT NOT NULL DEFAULT '');
CREATE TABLE capture_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    camera TEXT NOT NULL DEFAULT '',
    exp_seconds REAL NOT NULL DEFAULT 0,
    gain INTEGER NOT NULL DEFAULT 0,
    binning INTEGER NOT NULL DEFAULT 1,
    filter_set TEXT NOT NULL DEFAULT 'unknown',
    is_dark_profile INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile)
  );
CREATE INDEX idx_device_sources_active ON device_sources(is_active);
CREATE INDEX idx_targets_canonical_name ON targets(canonical_name);
CREATE INDEX idx_targets_category ON targets(category);
CREATE INDEX idx_capture_profiles_lookup ON capture_profiles(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile);
CREATE INDEX idx_sessions_source_id ON sessions(source_id);
CREATE INDEX idx_sessions_category ON sessions(category);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_filter_set ON sessions(filter_set);
CREATE INDEX idx_sessions_target_id ON sessions(target_id);
CREATE INDEX idx_sessions_capture_profile_id ON sessions(capture_profile_id);
CREATE INDEX idx_raw_files_source_id ON raw_files(source_id);
CREATE INDEX idx_raw_files_filter_set ON raw_files(filter_set);
CREATE INDEX idx_raw_files_status ON raw_files(file_status);
CREATE INDEX idx_raw_files_derivative_kind ON raw_files(derivative_kind);
CREATE INDEX idx_raw_files_bayerpat ON raw_files(header_bayerpat);
CREATE INDEX idx_cal_assets_source_id ON calibration_assets(source_id);
CREATE INDEX idx_targets_ra_dec ON targets(ra_deg, dec_deg);
CREATE INDEX idx_targets_coord_status ON targets(coord_status);
CREATE INDEX idx_targets_name_status ON targets(name_status);
CREATE INDEX idx_targets_wikidata_id ON targets(wikidata_id);
CREATE INDEX idx_targets_meta_status ON targets(meta_status);
CREATE INDEX idx_targets_ned_status ON targets(ned_status);
CREATE INDEX idx_targets_simbad_status ON targets(simbad_status);
CREATE INDEX idx_targets_nasa_status ON targets(nasa_status);
CREATE INDEX idx_targets_constellation ON targets(constellation);
