PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE sessions ADD COLUMN platesolve_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE sessions ADD COLUMN platesolve_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN platesolve_last_at TEXT;
ALTER TABLE sessions ADD COLUMN platesolve_reference_path TEXT;

ALTER TABLE sessions ADD COLUMN solve_ra_deg REAL;
ALTER TABLE sessions ADD COLUMN solve_dec_deg REAL;
ALTER TABLE sessions ADD COLUMN solve_fov_x_deg REAL;
ALTER TABLE sessions ADD COLUMN solve_fov_y_deg REAL;
ALTER TABLE sessions ADD COLUMN solve_rotation_deg REAL;

ALTER TABLE sessions ADD COLUMN solve_engine TEXT;
ALTER TABLE sessions ADD COLUMN solve_message TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_platesolve_status
    ON sessions(platesolve_status);

COMMIT;
PRAGMA foreign_keys=ON;
