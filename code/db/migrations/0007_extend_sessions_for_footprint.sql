PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE sessions ADD COLUMN corner_ul_ra_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_ul_dec_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_ur_ra_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_ur_dec_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_lr_ra_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_lr_dec_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_ll_ra_deg REAL;
ALTER TABLE sessions ADD COLUMN corner_ll_dec_deg REAL;

ALTER TABLE sessions ADD COLUMN footprint_radius_deg REAL;
ALTER TABLE sessions ADD COLUMN solve_pass TEXT;

ALTER TABLE sessions ADD COLUMN target_final TEXT;
ALTER TABLE sessions ADD COLUMN target_final_source TEXT;
ALTER TABLE sessions ADD COLUMN target_strategy TEXT;
ALTER TABLE sessions ADD COLUMN field_object_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN requested_target_found INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_sessions_solve_ra_dec
  ON sessions(solve_ra_deg, solve_dec_deg);

CREATE INDEX IF NOT EXISTS idx_sessions_target_final
  ON sessions(target_final);

COMMIT;
PRAGMA foreign_keys=ON;
