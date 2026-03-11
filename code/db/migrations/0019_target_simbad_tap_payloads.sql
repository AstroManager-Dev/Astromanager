PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_simbad_resolve ADD COLUMN maintype TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN rvz_radvel REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN rvz_redshift REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN rvz_type TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN rvz_error REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN rvz_qual TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN plx_err REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN nbref INTEGER;
ALTER TABLE target_simbad_resolve ADD COLUMN identifiers_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE target_simbad_resolve ADD COLUMN photometry_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE target_simbad_resolve ADD COLUMN tap_basic_json TEXT NOT NULL DEFAULT '{}';

COMMIT;
PRAGMA foreign_keys=ON;
