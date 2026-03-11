PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_sesame_resolve ADD COLUMN aliases TEXT NOT NULL DEFAULT '[]';

COMMIT;
PRAGMA foreign_keys=ON;
