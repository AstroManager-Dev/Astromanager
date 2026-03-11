PRAGMA foreign_keys=OFF;
BEGIN;

ALTER TABLE target_base_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_base_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_base_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_base_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_base_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_base_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_base_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_base_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_base_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_base_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_wikidata_name_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_name_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_wikidata_name_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_wikidata_name_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_name_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_wikidata_meta_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_wikidata_meta_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_simbad_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_simbad_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_simbad_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_ned_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_ned_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_ned_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_ned_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_ned_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_ned_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ned_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_constellation_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_constellation_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_constellation_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_constellation_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_constellation_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_constellation_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_nasa_resolve ADD COLUMN query_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_nasa_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_nasa_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_nasa_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_nasa_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_nasa_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_nasa_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_nasa_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_nasa_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_nasa_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_sesame_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_sesame_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_sesame_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_sesame_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_sesame_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_sesame_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_sesame_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_sesame_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_sesame_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_vizier_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_vizier_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_vizier_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_vizier_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_vizier_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_vizier_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_vizier_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_vizier_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_vizier_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_ssodnet_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_ssodnet_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_ssodnet_resolve ADD COLUMN position_source TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_ssodnet_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_skyview_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_skyview_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_skyview_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_skyview_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_skyview_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_skyview_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_skyview_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_skyview_resolve ADD COLUMN match_confidence REAL;

ALTER TABLE target_irsa_resolve ADD COLUMN query_ra_deg REAL;
ALTER TABLE target_irsa_resolve ADD COLUMN query_dec_deg REAL;
ALTER TABLE target_irsa_resolve ADD COLUMN match_name TEXT NOT NULL DEFAULT '';
ALTER TABLE target_irsa_resolve ADD COLUMN match_ra_deg REAL;
ALTER TABLE target_irsa_resolve ADD COLUMN match_dec_deg REAL;
ALTER TABLE target_irsa_resolve ADD COLUMN match_distance_deg REAL;
ALTER TABLE target_irsa_resolve ADD COLUMN match_method TEXT NOT NULL DEFAULT '';
ALTER TABLE target_irsa_resolve ADD COLUMN match_confidence REAL;

COMMIT;
PRAGMA foreign_keys=ON;
