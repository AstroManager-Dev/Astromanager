PRAGMA foreign_keys=OFF;
BEGIN;

CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    display_name TEXT,
    object_type TEXT,
    ra_deg REAL,
    dec_deg REAL,
    angular_size_arcmin REAL,
    source TEXT NOT NULL DEFAULT 'platesolve_field_match',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_targets_slug
ON targets(slug);

CREATE INDEX IF NOT EXISTS idx_targets_ra_dec
ON targets(ra_deg, dec_deg);

CREATE TABLE IF NOT EXISTS frame_targets (
    id INTEGER PRIMARY KEY,
    frame_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'platesolve_field_match',
    is_primary INTEGER NOT NULL DEFAULT 0,
    is_major INTEGER NOT NULL DEFAULT 0,
    is_requested_target INTEGER NOT NULL DEFAULT 0,
    priority_rank INTEGER,
    score REAL,
    distance_to_center_deg REAL,
    in_frame_fraction REAL,
    angular_size_arcmin REAL,
    ra_deg REAL,
    dec_deg REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (target_id) REFERENCES targets(id)
);

CREATE INDEX IF NOT EXISTS idx_frame_targets_frame_id
ON frame_targets(frame_id);

CREATE INDEX IF NOT EXISTS idx_frame_targets_target_id
ON frame_targets(target_id);

CREATE INDEX IF NOT EXISTS idx_session_targets_target_id
ON session_targets(target_id);

COMMIT;
PRAGMA foreign_keys=ON;
