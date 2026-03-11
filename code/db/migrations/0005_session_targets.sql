PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE sessions ADD COLUMN target_raw_source TEXT;
ALTER TABLE sessions ADD COLUMN target_final_source TEXT;
ALTER TABLE sessions ADD COLUMN target_strategy TEXT;
ALTER TABLE sessions ADD COLUMN target_conflict_flag INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN target_conflict_note TEXT;
ALTER TABLE sessions ADD COLUMN field_object_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN requested_target_found INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS session_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    target_id INTEGER,
    target_name TEXT NOT NULL,
    object_type TEXT,

    source TEXT NOT NULL,
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
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_session_targets_session_id
    ON session_targets(session_id);

CREATE INDEX IF NOT EXISTS idx_session_targets_target_name
    ON session_targets(target_name);

CREATE INDEX IF NOT EXISTS idx_session_targets_is_requested_target
    ON session_targets(is_requested_target);

CREATE INDEX IF NOT EXISTS idx_session_targets_priority_rank
    ON session_targets(session_id, priority_rank);

COMMIT;
PRAGMA foreign_keys=ON;
