PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_simbad_resolve ADD COLUMN aliases TEXT NOT NULL DEFAULT '[]';
ALTER TABLE target_simbad_resolve ADD COLUMN raw_payload TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN rv_value REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN rv_error REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN rv_quality TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN rv_ref TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN pmra REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN pmdec REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN plx_value REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN plx_error REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN bibcode_count REAL;

COMMIT;
PRAGMA foreign_keys=ON;
