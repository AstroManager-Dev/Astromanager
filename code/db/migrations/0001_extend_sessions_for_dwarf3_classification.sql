PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

ALTER TABLE sessions ADD COLUMN subtype TEXT;
ALTER TABLE sessions ADD COLUMN session_kind TEXT;
ALTER TABLE sessions ADD COLUMN target_source TEXT;
ALTER TABLE sessions ADD COLUMN solve_status TEXT NOT NULL DEFAULT 'review';
ALTER TABLE sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN needs_plate_solving INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN treat_as_normal_light INTEGER NOT NULL DEFAULT 1;
ALTER TABLE sessions ADD COLUMN classification_rule TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_subtype
  ON sessions(subtype);

CREATE INDEX IF NOT EXISTS idx_sessions_session_kind
  ON sessions(session_kind);

CREATE INDEX IF NOT EXISTS idx_sessions_target_source
  ON sessions(target_source);

CREATE INDEX IF NOT EXISTS idx_sessions_solve_status
  ON sessions(solve_status);

CREATE INDEX IF NOT EXISTS idx_sessions_review_flags
  ON sessions(needs_review, needs_plate_solving, treat_as_normal_light);

CREATE INDEX IF NOT EXISTS idx_sessions_kind_subtype
  ON sessions(session_kind, subtype);

COMMIT;
PRAGMA foreign_keys = ON;
