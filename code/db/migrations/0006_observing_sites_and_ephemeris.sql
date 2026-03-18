CREATE TABLE IF NOT EXISTS observing_sites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  latitude_deg REAL NOT NULL,
  longitude_deg REAL NOT NULL,
  elevation_m REAL,
  timezone_name TEXT NOT NULL DEFAULT '',
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

ALTER TABLE sessions ADD COLUMN observing_site_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_observing_sites_default ON observing_sites(is_default);
CREATE INDEX IF NOT EXISTS idx_sessions_observing_site_id ON sessions(observing_site_id);

CREATE TABLE IF NOT EXISTS session_moon_ephemeris (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL UNIQUE,
  site_id INTEGER,
  computed_at TEXT NOT NULL DEFAULT (datetime('now')),
  ephemeris_source TEXT NOT NULL DEFAULT 'swisseph',
  observation_time_utc TEXT NOT NULL DEFAULT '',
  computation_mode TEXT NOT NULL DEFAULT 'geocentric_fallback',
  moon_phase_name TEXT NOT NULL DEFAULT '',
  illumination_fraction REAL,
  moon_age_days REAL,
  distance_km REAL,
  angular_diameter_arcmin REAL,
  libration_lon_deg REAL,
  libration_lat_deg REAL,
  position_angle_deg REAL,
  colongitude_deg REAL,
  ra_deg REAL,
  dec_deg REAL,
  ecliptic_lon_deg REAL,
  ecliptic_lat_deg REAL,
  alt_deg REAL,
  az_deg REAL,
  rise_utc TEXT NOT NULL DEFAULT '',
  set_utc TEXT NOT NULL DEFAULT '',
  transit_utc TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (site_id) REFERENCES observing_sites(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_session_moon_ephemeris_site_id ON session_moon_ephemeris(site_id);

CREATE TABLE IF NOT EXISTS session_sun_ephemeris (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL UNIQUE,
  site_id INTEGER,
  computed_at TEXT NOT NULL DEFAULT (datetime('now')),
  ephemeris_source TEXT NOT NULL DEFAULT 'swisseph',
  observation_time_utc TEXT NOT NULL DEFAULT '',
  computation_mode TEXT NOT NULL DEFAULT 'geocentric_fallback',
  ra_deg REAL,
  dec_deg REAL,
  distance_au REAL,
  distance_km REAL,
  angular_diameter_arcmin REAL,
  p_angle_deg REAL,
  b0_deg REAL,
  l0_deg REAL,
  carrington_rotation REAL,
  central_meridian_lon_deg REAL,
  alt_deg REAL,
  az_deg REAL,
  airmass REAL,
  sunrise_utc TEXT NOT NULL DEFAULT '',
  sunset_utc TEXT NOT NULL DEFAULT '',
  transit_utc TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (site_id) REFERENCES observing_sites(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_session_sun_ephemeris_site_id ON session_sun_ephemeris(site_id);
