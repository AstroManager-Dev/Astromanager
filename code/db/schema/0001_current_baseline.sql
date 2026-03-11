PRAGMA foreign_keys=OFF;
BEGIN;

CREATE TABLE job_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_name TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT,
  source TEXT NOT NULL DEFAULT 'unknown',
  note TEXT DEFAULT '',
  stdout_log TEXT DEFAULT '',
  stderr_log TEXT DEFAULT ''
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE app_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE device_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_key TEXT NOT NULL UNIQUE,
  vendor TEXT NOT NULL,
  model TEXT NOT NULL,
  family TEXT NOT NULL DEFAULT 'smart_telescope',
  protocol TEXT NOT NULL DEFAULT '',
  root_pattern TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  session_key TEXT NOT NULL UNIQUE,
  session_type TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'unknown',
  raw_session_path TEXT NOT NULL UNIQUE,
  target TEXT NOT NULL,
  filter_set TEXT NOT NULL DEFAULT 'unknown',
  exp REAL,
  gain INTEGER,
  binning INTEGER,
  session_datetime TEXT NOT NULL,
  source_origin TEXT NOT NULL DEFAULT 'dwarf_sync',
  status TEXT NOT NULL DEFAULT 'indexed',
  frame_count INTEGER NOT NULL DEFAULT 0,
  total_bytes INTEGER NOT NULL DEFAULT 0,
  temp_min REAL,
  temp_max REAL,
  temp_avg REAL,
  has_dwarf_stack INTEGER NOT NULL DEFAULT 0,
  has_dwarf_preview INTEGER NOT NULL DEFAULT 0,
  has_dwarf_metadata INTEGER NOT NULL DEFAULT 0,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')), target_id INTEGER, capture_profile_id INTEGER, subtype TEXT, session_kind TEXT, target_source TEXT, solve_status TEXT NOT NULL DEFAULT 'review', needs_review INTEGER NOT NULL DEFAULT 0, needs_plate_solving INTEGER NOT NULL DEFAULT 0, treat_as_normal_light INTEGER NOT NULL DEFAULT 1, classification_rule TEXT, target_raw_source TEXT, target_final_source TEXT, target_strategy TEXT, target_conflict_flag INTEGER NOT NULL DEFAULT 0, target_conflict_note TEXT, field_object_count INTEGER NOT NULL DEFAULT 0, requested_target_found INTEGER NOT NULL DEFAULT 0, platesolve_status TEXT NOT NULL DEFAULT 'pending', platesolve_attempts INTEGER NOT NULL DEFAULT 0, platesolve_last_at TEXT, platesolve_reference_path TEXT, solve_ra_deg REAL, solve_dec_deg REAL, solve_fov_x_deg REAL, solve_fov_y_deg REAL, solve_rotation_deg REAL, solve_engine TEXT, solve_message TEXT, corner_ul_ra_deg REAL, corner_ul_dec_deg REAL, corner_ur_ra_deg REAL, corner_ur_dec_deg REAL, corner_lr_ra_deg REAL, corner_lr_dec_deg REAL, corner_ll_ra_deg REAL, corner_ll_dec_deg REAL, footprint_radius_deg REAL, solve_pass TEXT, target_final TEXT,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE raw_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  source_domain TEXT NOT NULL,
  source_subtype TEXT NOT NULL,
  abs_path TEXT NOT NULL UNIQUE,
  rel_path TEXT NOT NULL,
  parent_dir TEXT NOT NULL,
  file_name TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  mtime_epoch INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  session_key TEXT DEFAULT '',
  filter_set TEXT NOT NULL DEFAULT 'unknown',
  file_status TEXT NOT NULL DEFAULT 'ok',
  file_status_note TEXT DEFAULT '',
  derivative_kind TEXT NOT NULL DEFAULT '',
  is_session_input INTEGER NOT NULL DEFAULT 0,
  is_dwarf_generated INTEGER NOT NULL DEFAULT 0,
  header_object TEXT NOT NULL DEFAULT '',
  header_ra TEXT NOT NULL DEFAULT '',
  header_dec TEXT NOT NULL DEFAULT '',
  header_exptime REAL,
  header_gain REAL,
  header_filter TEXT NOT NULL DEFAULT '',
  header_date_obs TEXT NOT NULL DEFAULT '',
  header_bayerpat TEXT NOT NULL DEFAULT '',
  header_xbayroff INTEGER,
  header_ybayroff INTEGER,
  is_color_sensor INTEGER NOT NULL DEFAULT 0,
  debayer_required INTEGER NOT NULL DEFAULT 0,
  exp REAL,
  gain INTEGER,
  temp_c REAL,
  binning INTEGER,
  camera TEXT DEFAULT '',
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  is_current INTEGER NOT NULL DEFAULT 1, file_role TEXT, classification_rule TEXT, quality_flag TEXT,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE calibration_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL DEFAULT 1,
  asset_type TEXT NOT NULL,
  asset_origin TEXT NOT NULL,
  camera TEXT NOT NULL DEFAULT '',
  abs_path TEXT NOT NULL UNIQUE,
  rel_path TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  mtime_epoch INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  exp REAL,
  gain INTEGER,
  binning INTEGER,
  temp_c REAL,
  stack_count INTEGER,
  ir_index INTEGER,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  is_current INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);
CREATE TABLE targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  , ra_deg REAL, dec_deg REAL, coord_text TEXT NOT NULL DEFAULT '', coord_source TEXT NOT NULL DEFAULT '', coord_ref TEXT NOT NULL DEFAULT '', coord_status TEXT NOT NULL DEFAULT 'pending', name_status TEXT NOT NULL DEFAULT 'pending', name_source TEXT NOT NULL DEFAULT '', name_resolved_at TEXT, wikidata_id TEXT NOT NULL DEFAULT '', label_de TEXT NOT NULL DEFAULT '', label_en TEXT NOT NULL DEFAULT '', aliases_de TEXT NOT NULL DEFAULT '', aliases_en TEXT NOT NULL DEFAULT '', wiki_de_title TEXT NOT NULL DEFAULT '', wiki_en_title TEXT NOT NULL DEFAULT '', object_type TEXT NOT NULL DEFAULT '', mag_value REAL, mag_band TEXT NOT NULL DEFAULT '', distance_value REAL, distance_unit TEXT NOT NULL DEFAULT '', meta_status TEXT NOT NULL DEFAULT 'pending', meta_source TEXT NOT NULL DEFAULT '', meta_resolved_at TEXT, object_type_label_de TEXT NOT NULL DEFAULT '', object_type_label_en TEXT NOT NULL DEFAULT '', distance_unit_label_de TEXT NOT NULL DEFAULT '', distance_unit_label_en TEXT NOT NULL DEFAULT '', ned_preferred_name TEXT NOT NULL DEFAULT '', ned_objtype TEXT NOT NULL DEFAULT '', ned_ra_deg REAL, ned_dec_deg REAL, ned_redshift REAL, ned_status TEXT NOT NULL DEFAULT 'pending', ned_source TEXT NOT NULL DEFAULT '', ned_resolved_at TEXT, simbad_main_id TEXT NOT NULL DEFAULT '', simbad_otype TEXT NOT NULL DEFAULT '', simbad_ra_deg REAL, simbad_dec_deg REAL, simbad_status TEXT NOT NULL DEFAULT 'pending', simbad_source TEXT NOT NULL DEFAULT '', simbad_resolved_at TEXT, final_name TEXT NOT NULL DEFAULT '', final_objtype TEXT NOT NULL DEFAULT '', final_ra_deg REAL, final_dec_deg REAL, final_distance_value REAL, final_distance_unit TEXT NOT NULL DEFAULT '', final_source_summary TEXT NOT NULL DEFAULT '', nasa_image_url TEXT NOT NULL DEFAULT '', nasa_thumb_url TEXT NOT NULL DEFAULT '', nasa_title TEXT NOT NULL DEFAULT '', nasa_nasa_id TEXT NOT NULL DEFAULT '', nasa_status TEXT NOT NULL DEFAULT 'pending', nasa_source TEXT NOT NULL DEFAULT '', nasa_resolved_at TEXT, nasa_page_url TEXT NOT NULL DEFAULT '', nasa_asset_manifest_url TEXT NOT NULL DEFAULT '', distance_source TEXT NOT NULL DEFAULT '', distance_ref TEXT NOT NULL DEFAULT '', distance_ly REAL, identity_method TEXT NOT NULL DEFAULT '', identity_confidence REAL, coord_match_sep_arcsec REAL, constellation TEXT NOT NULL DEFAULT '', slug TEXT, angular_size_arcmin REAL, source TEXT NOT NULL DEFAULT 'platesolve_field_match');
CREATE TABLE capture_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    camera TEXT NOT NULL DEFAULT '',
    exp_seconds REAL NOT NULL DEFAULT 0,
    gain INTEGER NOT NULL DEFAULT 0,
    binning INTEGER NOT NULL DEFAULT 1,
    filter_set TEXT NOT NULL DEFAULT 'unknown',
    is_dark_profile INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile)
  );
CREATE INDEX idx_device_sources_active ON device_sources(is_active);
CREATE INDEX idx_targets_canonical_name ON targets(canonical_name);
CREATE INDEX idx_targets_category ON targets(category);
CREATE INDEX idx_capture_profiles_lookup ON capture_profiles(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile);
CREATE INDEX idx_sessions_source_id ON sessions(source_id);
CREATE INDEX idx_sessions_category ON sessions(category);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_filter_set ON sessions(filter_set);
CREATE INDEX idx_sessions_target_id ON sessions(target_id);
CREATE INDEX idx_sessions_capture_profile_id ON sessions(capture_profile_id);
CREATE INDEX idx_raw_files_source_id ON raw_files(source_id);
CREATE INDEX idx_raw_files_filter_set ON raw_files(filter_set);
CREATE INDEX idx_raw_files_status ON raw_files(file_status);
CREATE INDEX idx_raw_files_derivative_kind ON raw_files(derivative_kind);
CREATE INDEX idx_raw_files_bayerpat ON raw_files(header_bayerpat);
CREATE INDEX idx_cal_assets_source_id ON calibration_assets(source_id);
CREATE INDEX idx_targets_ra_dec ON targets(ra_deg, dec_deg);
CREATE INDEX idx_targets_coord_status ON targets(coord_status);
CREATE INDEX idx_targets_name_status ON targets(name_status);
CREATE INDEX idx_targets_wikidata_id ON targets(wikidata_id);
CREATE INDEX idx_targets_meta_status ON targets(meta_status);
CREATE INDEX idx_targets_ned_status ON targets(ned_status);
CREATE INDEX idx_targets_simbad_status ON targets(simbad_status);
CREATE INDEX idx_targets_nasa_status ON targets(nasa_status);
CREATE INDEX idx_targets_constellation ON targets(constellation);
CREATE INDEX idx_sessions_subtype
  ON sessions(subtype);
CREATE INDEX idx_sessions_session_kind
  ON sessions(session_kind);
CREATE INDEX idx_sessions_target_source
  ON sessions(target_source);
CREATE INDEX idx_sessions_solve_status
  ON sessions(solve_status);
CREATE INDEX idx_sessions_review_flags
  ON sessions(needs_review, needs_plate_solving, treat_as_normal_light);
CREATE INDEX idx_sessions_kind_subtype
  ON sessions(session_kind, subtype);
CREATE INDEX idx_raw_files_file_role
  ON raw_files(file_role);
CREATE INDEX idx_raw_files_classification_rule
  ON raw_files(classification_rule);
CREATE INDEX idx_raw_files_quality_flag
  ON raw_files(quality_flag);
CREATE TABLE session_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    target_id INTEGER,
    target_name TEXT NOT NULL,
    object_type TEXT,

    source TEXT NOT NULL,
    is_requested_target INTEGER NOT NULL DEFAULT 0,
    is_primary INTEGER NOT NULL DEFAULT 0,
    is_major INTEGER NOT NULL DEFAULT 0,

    priority_rank INTEGER,
    score REAL,

    distance_to_center_deg REAL,
    in_frame_fraction REAL,
    angular_size_arcmin REAL,

    ra_deg REAL,
    dec_deg REAL,

    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE SET NULL
);
CREATE INDEX idx_session_targets_session_id
    ON session_targets(session_id);
CREATE INDEX idx_session_targets_target_name
    ON session_targets(target_name);
CREATE INDEX idx_session_targets_is_requested_target
    ON session_targets(is_requested_target);
CREATE INDEX idx_session_targets_priority_rank
    ON session_targets(session_id, priority_rank);
CREATE INDEX idx_sessions_platesolve_status
    ON sessions(platesolve_status);
CREATE INDEX idx_sessions_solve_ra_dec
  ON sessions(solve_ra_deg, solve_dec_deg);
CREATE INDEX idx_sessions_target_final
  ON sessions(target_final);
CREATE TABLE frame_targets (
    id INTEGER PRIMARY KEY,
    frame_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'platesolve_field_match',
    is_primary INTEGER NOT NULL DEFAULT 0,
    is_major INTEGER NOT NULL DEFAULT 0,
    is_requested_target INTEGER NOT NULL DEFAULT 0,
    priority_rank INTEGER,
    score REAL,
    distance_to_center_deg REAL,
    in_frame_fraction REAL,
    angular_size_arcmin REAL,
    ra_deg REAL,
    dec_deg REAL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (target_id) REFERENCES targets(id)
);
CREATE INDEX idx_frame_targets_frame_id
ON frame_targets(frame_id);
CREATE INDEX idx_frame_targets_target_id
ON frame_targets(target_id);
CREATE INDEX idx_session_targets_target_id
ON session_targets(target_id);
CREATE UNIQUE INDEX idx_targets_slug ON targets(slug);
CREATE TABLE target_name_resolve (
      id INTEGER PRIMARY KEY,
      target_id INTEGER NOT NULL,
      canonical_name TEXT,
      slug TEXT,
      resolved_name TEXT,
      source TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      error_message TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
CREATE UNIQUE INDEX idx_target_name_resolve_target_id
      ON target_name_resolve(target_id);
CREATE TABLE target_meta_resolve (
      id INTEGER PRIMARY KEY,
      target_id INTEGER NOT NULL,
      canonical_name TEXT,
      slug TEXT,
      constellation TEXT,
      distance_label TEXT,
      source TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      error_message TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
CREATE UNIQUE INDEX idx_target_meta_resolve_target_id
      ON target_meta_resolve(target_id);
CREATE TABLE session_platesolve_resolve (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL UNIQUE,
  session_key TEXT,
  target TEXT,
  platesolve_status TEXT,
  platesolve_attempts INTEGER,
  platesolve_last_at TEXT,
  platesolve_reference_path TEXT,
  solve_ra_deg REAL,
  solve_dec_deg REAL,
  solve_fov_x_deg REAL,
  solve_fov_y_deg REAL,
  solve_rotation_deg REAL,
  footprint_radius_deg REAL,
  corner_ul_ra_deg REAL,
  corner_ul_dec_deg REAL,
  corner_ur_ra_deg REAL,
  corner_ur_dec_deg REAL,
  corner_lr_ra_deg REAL,
  corner_lr_dec_deg REAL,
  corner_ll_ra_deg REAL,
  corner_ll_dec_deg REAL,
  solve_engine TEXT,
  solve_message TEXT,
  solve_pass TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE session_target_resolve (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL UNIQUE,
  session_key TEXT,
  target_raw TEXT,
  target_final TEXT,
  target_final_source TEXT,
  target_strategy TEXT,
  field_object_count INTEGER,
  requested_target_found INTEGER,
  target_conflict_flag INTEGER,
  target_conflict_note TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE session_target_resolve_item (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  target_id INTEGER,
  target_name TEXT,
  object_type TEXT,
  source TEXT,
  is_requested_target INTEGER NOT NULL DEFAULT 0,
  is_primary INTEGER NOT NULL DEFAULT 0,
  is_major INTEGER NOT NULL DEFAULT 0,
  priority_rank INTEGER,
  score REAL,
  distance_to_center_deg REAL,
  in_frame_fraction REAL,
  angular_size_arcmin REAL,
  ra_deg REAL,
  dec_deg REAL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_session_target_resolve_item_session_id
  ON session_target_resolve_item(session_id);
CREATE INDEX idx_session_target_resolve_item_target_id
  ON session_target_resolve_item(target_id);
CREATE TABLE target_base_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  display_name TEXT,
  category TEXT,
  ra_deg REAL,
  dec_deg REAL,
  coord_text TEXT,
  coord_ref TEXT,
  status TEXT,
  source TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE TABLE target_wikidata_name_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  wikidata_id TEXT,
  label_de TEXT,
  label_en TEXT,
  aliases_de TEXT,
  aliases_en TEXT,
  wiki_de_title TEXT,
  wiki_en_title TEXT,
  resolved_name TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE TABLE target_wikidata_meta_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  wikidata_id TEXT,
  object_type TEXT,
  object_type_label_de TEXT,
  object_type_label_en TEXT,
  mag_value REAL,
  mag_band TEXT,
  distance_value REAL,
  distance_unit TEXT,
  distance_unit_label_de TEXT,
  distance_unit_label_en TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE TABLE target_simbad_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  simbad_main_id TEXT,
  simbad_otype TEXT,
  simbad_ra_deg REAL,
  simbad_dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL, aliases TEXT NOT NULL DEFAULT '[]', raw_payload TEXT NOT NULL DEFAULT '', rv_value REAL, rv_error REAL, rv_quality TEXT NOT NULL DEFAULT '', rv_ref TEXT NOT NULL DEFAULT '', pmra REAL, pmdec REAL, plx_value REAL, plx_error REAL, bibcode_count REAL, maintype TEXT NOT NULL DEFAULT '', rvz_radvel REAL, rvz_redshift REAL, rvz_type TEXT NOT NULL DEFAULT '', rvz_error REAL, rvz_qual TEXT NOT NULL DEFAULT '', plx_err REAL, nbref INTEGER, identifiers_json TEXT NOT NULL DEFAULT '[]', photometry_json TEXT NOT NULL DEFAULT '{}', tap_basic_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE target_ned_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  ned_objtype TEXT,
  ned_ra_deg REAL,
  ned_dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL, ned_preferred_name TEXT NOT NULL DEFAULT '', ned_interpreted_name TEXT NOT NULL DEFAULT '', ned_position_refcode TEXT NOT NULL DEFAULT '', ned_objtype_refcode TEXT NOT NULL DEFAULT '', ned_redshift REAL, ned_redshift_uncertainty REAL, ned_redshift_refcode TEXT NOT NULL DEFAULT '', ned_redshift_quality TEXT NOT NULL DEFAULT '', ned_status_code TEXT, ned_result_code TEXT, ned_resolver_name TEXT NOT NULL DEFAULT '', raw_payload TEXT NOT NULL DEFAULT '');
CREATE TABLE target_constellation_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  constellation_name TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL, constellation_code TEXT NOT NULL DEFAULT '', ra_deg REAL, dec_deg REAL);
CREATE TABLE target_nasa_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  nasa_title TEXT,
  nasa_page_url TEXT,
  nasa_image_url TEXT,
  nasa_thumb_url TEXT,
  status TEXT,
  source TEXT,
  error_message TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_name TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE INDEX idx_target_base_resolve_target_id
  ON target_base_resolve(target_id);
CREATE INDEX idx_target_wikidata_name_resolve_target_id
  ON target_wikidata_name_resolve(target_id);
CREATE INDEX idx_target_wikidata_meta_resolve_target_id
  ON target_wikidata_meta_resolve(target_id);
CREATE INDEX idx_target_simbad_resolve_target_id
  ON target_simbad_resolve(target_id);
CREATE INDEX idx_target_ned_resolve_target_id
  ON target_ned_resolve(target_id);
CREATE INDEX idx_target_constellation_resolve_target_id
  ON target_constellation_resolve(target_id);
CREATE INDEX idx_target_nasa_resolve_target_id
  ON target_nasa_resolve(target_id);
CREATE TABLE target_skyview_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  survey TEXT NOT NULL DEFAULT 'DSS2 Color',
  position_source TEXT NOT NULL DEFAULT '',
  ra_deg REAL,
  dec_deg REAL,
  image_url TEXT NOT NULL DEFAULT '',
  fits_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_ra_deg REAL, query_dec_deg REAL, match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE INDEX idx_target_skyview_resolve_status
  ON target_skyview_resolve(status);
CREATE TABLE target_irsa_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  position_source TEXT NOT NULL DEFAULT '',
  ra_deg REAL,
  dec_deg REAL,
  viewer_url TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_ra_deg REAL, query_dec_deg REAL, match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE INDEX idx_target_irsa_resolve_status
  ON target_irsa_resolve(status);
CREATE TABLE target_sesame_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  resolver_name TEXT,
  sesame_oid TEXT,
  sesame_oname TEXT,
  sesame_otype TEXT,
  sesame_mtype TEXT,
  ra_deg REAL,
  dec_deg REAL,
  coord_text TEXT,
  coord_ref TEXT,
  vel_value REAL,
  vel_error REAL,
  vel_quality TEXT,
  vel_ref TEXT,
  nrefs INTEGER,
  status TEXT,
  source TEXT,
  error_message TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL, aliases TEXT NOT NULL DEFAULT '[]');
CREATE TABLE target_vizier_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  catalog_source TEXT,
  main_id TEXT,
  preferred_name TEXT,
  aliases TEXT,
  object_type TEXT,
  object_type_label TEXT,
  ra_deg REAL,
  dec_deg REAL,
  ra_text TEXT,
  dec_text TEXT,
  magnitude_value REAL,
  magnitude_band TEXT,
  distance_value REAL,
  distance_unit TEXT,
  identifier_count INTEGER,
  status TEXT,
  source TEXT,
  error_message TEXT,
  request_url TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, resource_name TEXT NOT NULL DEFAULT '', resource_title TEXT NOT NULL DEFAULT '', resource_ivoid TEXT NOT NULL DEFAULT '', data_ivoid TEXT NOT NULL DEFAULT '', creator TEXT NOT NULL DEFAULT '', bibcode TEXT NOT NULL DEFAULT '', journal TEXT NOT NULL DEFAULT '', original_date TEXT NOT NULL DEFAULT '', reference_url TEXT NOT NULL DEFAULT '', publication_date TEXT NOT NULL DEFAULT '', rights_uri TEXT NOT NULL DEFAULT '', table_name TEXT NOT NULL DEFAULT '', catalog_code TEXT NOT NULL DEFAULT '', ngc_ic TEXT NOT NULL DEFAULT '', ngc_ic_component TEXT NOT NULL DEFAULT '', ra_b1950 TEXT NOT NULL DEFAULT '', dec_b1950 TEXT NOT NULL DEFAULT '', pos_quality TEXT NOT NULL DEFAULT '', pos_flag TEXT NOT NULL DEFAULT '', pos_ref TEXT NOT NULL DEFAULT '', obs_count INTEGER, comment_text TEXT NOT NULL DEFAULT '', simbad_ref TEXT NOT NULL DEFAULT '', ned_ref TEXT NOT NULL DEFAULT '', ra_icrs_text TEXT NOT NULL DEFAULT '', dec_icrs_text TEXT NOT NULL DEFAULT '', query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL, catalog_name TEXT NOT NULL DEFAULT '', catalog_table TEXT NOT NULL DEFAULT '');
CREATE TABLE target_ssodnet_resolve (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,
  canonical_name TEXT,
  slug TEXT,
  query_name TEXT,
  resolver_id TEXT,
  object_type TEXT,
  object_class TEXT,
  display_name TEXT,
  number_text TEXT,
  title TEXT,
  aliases TEXT,
  parent_name TEXT,
  system_name TEXT,
  has_ephemeris INTEGER NOT NULL DEFAULT 0,
  has_physical_ephemeris INTEGER NOT NULL DEFAULT 0,
  has_physical_models INTEGER NOT NULL DEFAULT 0,
  ra_deg REAL,
  dec_deg REAL,
  status TEXT,
  source TEXT,
  error_message TEXT,
  raw_payload TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
, query_ra_deg REAL, query_dec_deg REAL, position_source TEXT NOT NULL DEFAULT '', match_name TEXT NOT NULL DEFAULT '', match_ra_deg REAL, match_dec_deg REAL, match_distance_deg REAL, match_method TEXT NOT NULL DEFAULT '', match_confidence REAL);
CREATE INDEX idx_target_sesame_resolve_target_id
  ON target_sesame_resolve(target_id);
CREATE INDEX idx_target_sesame_resolve_status
  ON target_sesame_resolve(status);
CREATE INDEX idx_target_vizier_resolve_target_id
  ON target_vizier_resolve(target_id);
CREATE INDEX idx_target_vizier_resolve_status
  ON target_vizier_resolve(status);
CREATE INDEX idx_target_ssodnet_resolve_target_id
  ON target_ssodnet_resolve(target_id);
CREATE INDEX idx_target_ssodnet_resolve_status
  ON target_ssodnet_resolve(status);
CREATE TABLE external_source_state (
  id INTEGER PRIMARY KEY,
  source_key TEXT NOT NULL UNIQUE,
  source_url TEXT NOT NULL DEFAULT '',
  local_path TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  last_checked_at TEXT,
  last_downloaded_at TEXT,
  expires_at TEXT,
  etag TEXT NOT NULL DEFAULT '',
  last_modified TEXT NOT NULL DEFAULT '',
  error_message TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_external_source_state_source_key
  ON external_source_state(source_key);
CREATE INDEX idx_target_constellation_resolve_status
  ON target_constellation_resolve(status);
CREATE INDEX idx_target_constellation_resolve_code
  ON target_constellation_resolve(constellation_code);
CREATE TABLE target_final (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL UNIQUE,

  canonical_name TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  slug TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',

  final_name TEXT NOT NULL DEFAULT '',
  final_name_source TEXT NOT NULL DEFAULT '',

  final_objtype TEXT NOT NULL DEFAULT '',
  final_objtype_source TEXT NOT NULL DEFAULT '',

  final_ra_deg REAL,
  final_dec_deg REAL,
  final_coord_source TEXT NOT NULL DEFAULT '',

  final_distance_value REAL,
  final_distance_unit TEXT NOT NULL DEFAULT '',
  distance_ly REAL,
  distance_source TEXT NOT NULL DEFAULT '',
  distance_ref TEXT NOT NULL DEFAULT '',

  mag_value REAL,
  mag_band TEXT NOT NULL DEFAULT '',
  mag_source TEXT NOT NULL DEFAULT '',

  constellation_code TEXT NOT NULL DEFAULT '',
  constellation_name TEXT NOT NULL DEFAULT '',
  constellation_source TEXT NOT NULL DEFAULT '',

  identity_method TEXT NOT NULL DEFAULT '',
  identity_confidence REAL,
  coord_match_sep_arcsec REAL,
  angular_size_arcmin REAL,

  final_source_summary TEXT NOT NULL DEFAULT '',
  merge_status TEXT NOT NULL DEFAULT 'pending',
  merge_notes TEXT NOT NULL DEFAULT '',

  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
);
CREATE INDEX idx_target_final_target_id
  ON target_final(target_id);
CREATE INDEX idx_target_final_name
  ON target_final(final_name);
CREATE INDEX idx_target_final_category
  ON target_final(category);
CREATE INDEX idx_target_final_constellation_code
  ON target_final(constellation_code);
CREATE INDEX idx_target_final_merge_status
  ON target_final(merge_status);

COMMIT;
PRAGMA foreign_keys=ON;
