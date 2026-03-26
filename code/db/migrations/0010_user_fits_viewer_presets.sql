CREATE TABLE IF NOT EXISTS user_fits_viewer_presets (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  preset_key TEXT NOT NULL,
  label TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 1000,
  is_active INTEGER NOT NULL DEFAULT 1,
  debayer_mode TEXT NOT NULL DEFAULT 'auto',
  stretch_mode TEXT NOT NULL DEFAULT 'auto',
  black_value REAL NOT NULL DEFAULT 0.5,
  white_value REAL NOT NULL DEFAULT 99.5,
  gamma_value REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, preset_key)
);

CREATE INDEX IF NOT EXISTS idx_user_fits_viewer_presets_owner
  ON user_fits_viewer_presets(user_id, is_active, sort_order, label);
