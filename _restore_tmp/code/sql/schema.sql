PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS job_runs (
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

CREATE TABLE IF NOT EXISTS app_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS device_sources (
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

CREATE TABLE IF NOT EXISTS sessions (
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
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);

CREATE TABLE IF NOT EXISTS raw_files (
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

CREATE TABLE IF NOT EXISTS calibration_assets (
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

CREATE INDEX IF NOT EXISTS idx_device_sources_active ON device_sources(is_active);

CREATE INDEX IF NOT EXISTS idx_sessions_source_id ON sessions(source_id);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(category);
CREATE INDEX IF NOT EXISTS idx_sessions_target ON sessions(target);
CREATE INDEX IF NOT EXISTS idx_sessions_filter_set ON sessions(filter_set);
CREATE INDEX IF NOT EXISTS idx_sessions_exp_gain ON sessions(exp, gain);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

CREATE INDEX IF NOT EXISTS idx_raw_files_source_id ON raw_files(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_files_domain ON raw_files(source_domain);
CREATE INDEX IF NOT EXISTS idx_raw_files_session_key ON raw_files(session_key);
CREATE INDEX IF NOT EXISTS idx_raw_files_filter_set ON raw_files(filter_set);
CREATE INDEX IF NOT EXISTS idx_raw_files_status ON raw_files(file_status);
CREATE INDEX IF NOT EXISTS idx_raw_files_derivative_kind ON raw_files(derivative_kind);
CREATE INDEX IF NOT EXISTS idx_raw_files_sha256 ON raw_files(sha256);
CREATE INDEX IF NOT EXISTS idx_raw_files_bayerpat ON raw_files(header_bayerpat);

CREATE INDEX IF NOT EXISTS idx_cal_assets_source_id ON calibration_assets(source_id);
CREATE INDEX IF NOT EXISTS idx_cal_assets_type ON calibration_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_cal_assets_origin ON calibration_assets(asset_origin);
CREATE INDEX IF NOT EXISTS idx_cal_assets_exp_gain ON calibration_assets(exp, gain);
