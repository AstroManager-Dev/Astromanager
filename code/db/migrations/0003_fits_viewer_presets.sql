CREATE TABLE IF NOT EXISTS fits_viewer_presets (
  id INTEGER PRIMARY KEY,
  preset_key TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 100,
  is_active INTEGER NOT NULL DEFAULT 1,
  is_system INTEGER NOT NULL DEFAULT 1,
  debayer_mode TEXT NOT NULL DEFAULT 'auto',
  stretch_mode TEXT NOT NULL DEFAULT 'auto',
  black_value REAL NOT NULL DEFAULT 0.5,
  white_value REAL NOT NULL DEFAULT 99.5,
  gamma_value REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fits_viewer_presets_active
  ON fits_viewer_presets(is_active, sort_order, label);

INSERT INTO fits_viewer_presets (preset_key, label, description, sort_order, is_active, is_system, debayer_mode, stretch_mode, black_value, white_value, gamma_value)
VALUES
  ('auto', 'Auto', 'Automatische Auswahl anhand der RAW-Metadaten.', 10, 1, 1, 'auto', 'auto', 0.5, 99.5, 1.0),
  ('neutral', 'Neutral', 'Universelle Vorschau mit moderatem Stretch.', 20, 1, 1, 'auto', 'arcsinh', 0.5, 99.5, 1.0),
  ('nebula', 'Nebula', 'Mehr Betonung schwacher Nebelbereiche.', 30, 1, 1, 'auto', 'arcsinh', 1.2, 99.8, 0.93),
  ('moon_planet', 'Moon / Planet', 'Kontrastreichere Vorschau für helle Objekte.', 40, 1, 1, 'mono', 'linear', 0.1, 99.0, 0.85),
  ('linear', 'Linear', 'Nahe am linearen Rohbild mit wenig Stretch.', 50, 1, 1, 'auto', 'linear', 0.2, 99.7, 1.0)
ON CONFLICT(preset_key) DO UPDATE SET
  label=excluded.label,
  description=excluded.description,
  sort_order=excluded.sort_order,
  is_active=excluded.is_active,
  is_system=excluded.is_system,
  debayer_mode=excluded.debayer_mode,
  stretch_mode=excluded.stretch_mode,
  black_value=excluded.black_value,
  white_value=excluded.white_value,
  gamma_value=excluded.gamma_value,
  updated_at=datetime('now');
