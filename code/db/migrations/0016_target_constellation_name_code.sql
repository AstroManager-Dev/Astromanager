PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_constellation_resolve RENAME COLUMN constellation TO constellation_name;
ALTER TABLE target_constellation_resolve ADD COLUMN constellation_code TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_target_constellation_resolve_status
  ON target_constellation_resolve(status);

CREATE INDEX IF NOT EXISTS idx_target_constellation_resolve_code
  ON target_constellation_resolve(constellation_code);

COMMIT;
PRAGMA foreign_keys=ON;
