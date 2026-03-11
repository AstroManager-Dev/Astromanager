ALTER TABLE target_constellation_resolve ADD COLUMN ra_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN dec_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_constellation_resolve ADD COLUMN error_message TEXT NOT NULL DEFAULT '';
