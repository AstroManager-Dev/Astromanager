PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_ned_resolve ADD COLUMN ned_preferred_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_interpreted_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_position_refcode TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_objtype_refcode TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_redshift REAL;
ALTER TABLE target_ned_resolve ADD COLUMN ned_redshift_uncertainty REAL;
ALTER TABLE target_ned_resolve ADD COLUMN ned_redshift_refcode TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_redshift_quality TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN ned_status_code TEXT;
ALTER TABLE target_ned_resolve ADD COLUMN ned_result_code TEXT;
ALTER TABLE target_ned_resolve ADD COLUMN ned_resolver_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN raw_payload TEXT NOT NULL DEFAULT '';

COMMIT;
PRAGMA foreign_keys=ON;
