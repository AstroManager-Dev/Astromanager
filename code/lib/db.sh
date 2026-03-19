#!/usr/bin/env bash
set -euo pipefail

db_require() {
  : "${DB_PATH:?DB_PATH is not set}"
  mkdir -p "$(dirname "$DB_PATH")"
}

db_column_exists() {
  local table="$1" column="$2"
  sqlite3 "$DB_PATH" "PRAGMA table_info(${table});" | awk -F'|' -v col="$column" '$2 == col { found=1 } END { exit(found ? 0 : 1) }'
}

db_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

db_exec() {
  db_require
  sqlite3 "$DB_PATH" "$1"
}


db_apply_migrations() {
  local root="${1:-/app}"
  local mig_dir="$root/db/migrations"

  db_exec "CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
  );"

  [[ -d "$mig_dir" ]] || return 0

  local migration_file migration_name
  while IFS= read -r migration_file; do
    [[ -n "$migration_file" ]] || continue
    migration_name="$(basename "$migration_file")"
    if db_exec "SELECT 1 FROM schema_migrations WHERE migration_name='$(db_escape "$migration_name")' LIMIT 1;" | grep -q 1; then
      continue
    fi
    sqlite3 "$DB_PATH" < "$migration_file"
    db_exec "INSERT INTO schema_migrations (migration_name) VALUES ('$(db_escape "$migration_name")');"
  done < <(find "$mig_dir" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sql' | sort)
}

db_seed_device_sources() {
  db_exec "
    INSERT INTO device_sources (
      id, source_key, vendor, model, family, protocol, root_pattern,
      remote_base_dir, allowed_extensions, notes, is_active, created_at, updated_at
    )
    VALUES
      (
        1, 'dwarflab_dwarf3', 'Dwarflab', 'DWARF3', 'smart_telescope', 'ftp',
        'DWARF_RAW_TELE*|DWARF_DARK|CALI_FRAME', '/Astronomy',
        '.fits,.fit,.fts,.jpg,.jpeg,.png,.json,.tif,.tiff',
        'default current source', 1, datetime('now'), datetime('now')
      ),
      (
        2, 'dwarflab_dwarf2', 'Dwarflab', 'DWARF2', 'smart_telescope', 'ftp',
        '', '/Astronomy', '.fits,.fit,.fts', '', 1, datetime('now'), datetime('now')
      ),
      (
        3, 'dwarflab_dwarf_mini', 'Dwarflab', 'DWARF Mini', 'smart_telescope', 'ftp',
        '', '/Astronomy', '.fits,.fit,.fts', '', 1, datetime('now'), datetime('now')
      ),
      (
        4, 'zwo_seestar_s50', 'ZWO', 'Seestar S50', 'smart_telescope', 'ftp',
        '', '/Astronomy', '.fits,.fit,.fts,.jpg,.jpeg,.png,.json', '', 1, datetime('now'), datetime('now')
      )
    ON CONFLICT(source_key) DO UPDATE SET
      vendor=excluded.vendor,
      model=excluded.model,
      family=excluded.family,
      protocol=excluded.protocol,
      root_pattern=excluded.root_pattern,
      remote_base_dir=excluded.remote_base_dir,
      allowed_extensions=excluded.allowed_extensions,
      notes=excluded.notes,
      is_active=excluded.is_active,
      updated_at=datetime('now','localtime');
  "
}

db_seed_device_instances() {
  db_exec "
    INSERT INTO device_instances (
      instance_key, display_name, source_id, connection_kind, host, port,
      auth_mode, username, password_text, timeout_seconds, is_active, is_default,
      created_at, updated_at
    )
    SELECT
      'dwarflab_dwarf3', 'DWARF 3', ds.id, 'ftp', '192.168.2.163', 21,
      'anonymous', 'anonymous', '', 15, 1, 1,
      datetime('now'), datetime('now')
    FROM device_sources ds
    WHERE ds.source_key = 'dwarflab_dwarf3'
    ON CONFLICT(instance_key) DO UPDATE SET
      display_name=excluded.display_name,
      source_id=excluded.source_id,
      connection_kind=excluded.connection_kind,
      host=excluded.host,
      port=excluded.port,
      auth_mode=excluded.auth_mode,
      username=excluded.username,
      password_text=excluded.password_text,
      timeout_seconds=excluded.timeout_seconds,
      is_active=excluded.is_active,
      is_default=excluded.is_default,
      updated_at=datetime('now','localtime');
  "
}

db_init() {
  local root="${1:-/app}"
  db_require

  if [[ ! -f "$root/sql/schema.sql" ]]; then
    echo "db_init: missing schema: $root/sql/schema.sql" >&2
    exit 23
  fi

  grep -viE '^[[:space:]]*CREATE[[:space:]]+INDEX' "$root/sql/schema.sql" | sqlite3 "$DB_PATH"

  db_exec "CREATE TABLE IF NOT EXISTS device_sources (
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
  );"


  db_exec "CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );"




  for c in ra_deg dec_deg coord_text coord_source coord_ref; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        ra_deg) db_exec "ALTER TABLE targets ADD COLUMN ra_deg REAL;" ;;
        dec_deg) db_exec "ALTER TABLE targets ADD COLUMN dec_deg REAL;" ;;
        coord_text) db_exec "ALTER TABLE targets ADD COLUMN coord_text TEXT NOT NULL DEFAULT '';" ;;
        coord_source) db_exec "ALTER TABLE targets ADD COLUMN coord_source TEXT NOT NULL DEFAULT '';" ;;
        coord_ref) db_exec "ALTER TABLE targets ADD COLUMN coord_ref TEXT NOT NULL DEFAULT '';" ;;
      esac
    fi
  done


db_exec "CREATE TABLE IF NOT EXISTS capture_profiles (
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
  );"

  for c in category filter_set temp_min temp_max temp_avg source_id has_dwarf_stack has_dwarf_preview has_dwarf_metadata target_id capture_profile_id; do
    if ! db_column_exists sessions "$c"; then
      case "$c" in
        category) db_exec "ALTER TABLE sessions ADD COLUMN category TEXT NOT NULL DEFAULT 'unknown';" ;;
        filter_set) db_exec "ALTER TABLE sessions ADD COLUMN filter_set TEXT NOT NULL DEFAULT 'unknown';" ;;
        temp_min) db_exec "ALTER TABLE sessions ADD COLUMN temp_min REAL;" ;;
        temp_max) db_exec "ALTER TABLE sessions ADD COLUMN temp_max REAL;" ;;
        temp_avg) db_exec "ALTER TABLE sessions ADD COLUMN temp_avg REAL;" ;;
        source_id) db_exec "ALTER TABLE sessions ADD COLUMN source_id INTEGER NOT NULL DEFAULT 1;" ;;
        has_dwarf_stack) db_exec "ALTER TABLE sessions ADD COLUMN has_dwarf_stack INTEGER NOT NULL DEFAULT 0;" ;;
        has_dwarf_preview) db_exec "ALTER TABLE sessions ADD COLUMN has_dwarf_preview INTEGER NOT NULL DEFAULT 0;" ;;
        has_dwarf_metadata) db_exec "ALTER TABLE sessions ADD COLUMN has_dwarf_metadata INTEGER NOT NULL DEFAULT 0;" ;;
        target_id) db_exec "ALTER TABLE sessions ADD COLUMN target_id INTEGER;" ;;
        capture_profile_id) db_exec "ALTER TABLE sessions ADD COLUMN capture_profile_id INTEGER;" ;;
      esac
    fi
  done

  for c in filter_set file_status file_status_note derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat header_xbayroff header_ybayroff is_color_sensor debayer_required source_id; do
    if ! db_column_exists raw_files "$c"; then
      case "$c" in
        filter_set) db_exec "ALTER TABLE raw_files ADD COLUMN filter_set TEXT NOT NULL DEFAULT 'unknown';" ;;
        file_status) db_exec "ALTER TABLE raw_files ADD COLUMN file_status TEXT NOT NULL DEFAULT 'ok';" ;;
        file_status_note) db_exec "ALTER TABLE raw_files ADD COLUMN file_status_note TEXT DEFAULT '';" ;;
        derivative_kind) db_exec "ALTER TABLE raw_files ADD COLUMN derivative_kind TEXT NOT NULL DEFAULT '';" ;;
        is_session_input) db_exec "ALTER TABLE raw_files ADD COLUMN is_session_input INTEGER NOT NULL DEFAULT 0;" ;;
        is_dwarf_generated) db_exec "ALTER TABLE raw_files ADD COLUMN is_dwarf_generated INTEGER NOT NULL DEFAULT 0;" ;;
        header_object) db_exec "ALTER TABLE raw_files ADD COLUMN header_object TEXT NOT NULL DEFAULT '';" ;;
        header_ra) db_exec "ALTER TABLE raw_files ADD COLUMN header_ra TEXT NOT NULL DEFAULT '';" ;;
        header_dec) db_exec "ALTER TABLE raw_files ADD COLUMN header_dec TEXT NOT NULL DEFAULT '';" ;;
        header_exptime) db_exec "ALTER TABLE raw_files ADD COLUMN header_exptime REAL;" ;;
        header_gain) db_exec "ALTER TABLE raw_files ADD COLUMN header_gain REAL;" ;;
        header_filter) db_exec "ALTER TABLE raw_files ADD COLUMN header_filter TEXT NOT NULL DEFAULT '';" ;;
        header_date_obs) db_exec "ALTER TABLE raw_files ADD COLUMN header_date_obs TEXT NOT NULL DEFAULT '';" ;;
        header_bayerpat) db_exec "ALTER TABLE raw_files ADD COLUMN header_bayerpat TEXT NOT NULL DEFAULT '';" ;;
        header_xbayroff) db_exec "ALTER TABLE raw_files ADD COLUMN header_xbayroff INTEGER;" ;;
        header_ybayroff) db_exec "ALTER TABLE raw_files ADD COLUMN header_ybayroff INTEGER;" ;;
        is_color_sensor) db_exec "ALTER TABLE raw_files ADD COLUMN is_color_sensor INTEGER NOT NULL DEFAULT 0;" ;;
        debayer_required) db_exec "ALTER TABLE raw_files ADD COLUMN debayer_required INTEGER NOT NULL DEFAULT 0;" ;;
        source_id) db_exec "ALTER TABLE raw_files ADD COLUMN source_id INTEGER NOT NULL DEFAULT 1;" ;;
      esac
    fi
  done

  if ! db_column_exists calibration_assets source_id; then
    db_exec "ALTER TABLE calibration_assets ADD COLUMN source_id INTEGER NOT NULL DEFAULT 1;"
  fi

  db_exec "CREATE INDEX IF NOT EXISTS idx_device_sources_active ON device_sources(is_active);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_canonical_name ON targets(canonical_name);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_ra_dec ON targets(ra_deg, dec_deg);"

  for c in coord_status name_status name_source name_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        coord_status) db_exec "ALTER TABLE targets ADD COLUMN coord_status TEXT NOT NULL DEFAULT 'pending';" ;;
        name_status) db_exec "ALTER TABLE targets ADD COLUMN name_status TEXT NOT NULL DEFAULT 'pending';" ;;
        name_source) db_exec "ALTER TABLE targets ADD COLUMN name_source TEXT NOT NULL DEFAULT '';" ;;
        name_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN name_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_coord_status ON targets(coord_status);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_name_status ON targets(name_status);"

  db_apply_migrations "$root"

  for c in wikidata_id label_de label_en aliases_de aliases_en wiki_de_title wiki_en_title object_type mag_value mag_band distance_value distance_unit meta_status meta_source meta_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        wikidata_id) db_exec "ALTER TABLE targets ADD COLUMN wikidata_id TEXT NOT NULL DEFAULT '';" ;;
        label_de) db_exec "ALTER TABLE targets ADD COLUMN label_de TEXT NOT NULL DEFAULT '';" ;;
        label_en) db_exec "ALTER TABLE targets ADD COLUMN label_en TEXT NOT NULL DEFAULT '';" ;;
        aliases_de) db_exec "ALTER TABLE targets ADD COLUMN aliases_de TEXT NOT NULL DEFAULT '';" ;;
        aliases_en) db_exec "ALTER TABLE targets ADD COLUMN aliases_en TEXT NOT NULL DEFAULT '';" ;;
        wiki_de_title) db_exec "ALTER TABLE targets ADD COLUMN wiki_de_title TEXT NOT NULL DEFAULT '';" ;;
        wiki_en_title) db_exec "ALTER TABLE targets ADD COLUMN wiki_en_title TEXT NOT NULL DEFAULT '';" ;;
        object_type) db_exec "ALTER TABLE targets ADD COLUMN object_type TEXT NOT NULL DEFAULT '';" ;;
        mag_value) db_exec "ALTER TABLE targets ADD COLUMN mag_value REAL;" ;;
        mag_band) db_exec "ALTER TABLE targets ADD COLUMN mag_band TEXT NOT NULL DEFAULT '';" ;;
        distance_value) db_exec "ALTER TABLE targets ADD COLUMN distance_value REAL;" ;;
        distance_unit) db_exec "ALTER TABLE targets ADD COLUMN distance_unit TEXT NOT NULL DEFAULT '';" ;;
        meta_status) db_exec "ALTER TABLE targets ADD COLUMN meta_status TEXT NOT NULL DEFAULT 'pending';" ;;
        meta_source) db_exec "ALTER TABLE targets ADD COLUMN meta_source TEXT NOT NULL DEFAULT '';" ;;
        meta_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN meta_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_wikidata_id ON targets(wikidata_id);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_meta_status ON targets(meta_status);"

  for c in ned_preferred_name ned_objtype ned_ra_deg ned_dec_deg ned_redshift ned_status ned_source ned_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        ned_preferred_name) db_exec "ALTER TABLE targets ADD COLUMN ned_preferred_name TEXT NOT NULL DEFAULT '';" ;;
        ned_objtype) db_exec "ALTER TABLE targets ADD COLUMN ned_objtype TEXT NOT NULL DEFAULT '';" ;;
        ned_ra_deg) db_exec "ALTER TABLE targets ADD COLUMN ned_ra_deg REAL;" ;;
        ned_dec_deg) db_exec "ALTER TABLE targets ADD COLUMN ned_dec_deg REAL;" ;;
        ned_redshift) db_exec "ALTER TABLE targets ADD COLUMN ned_redshift REAL;" ;;
        ned_status) db_exec "ALTER TABLE targets ADD COLUMN ned_status TEXT NOT NULL DEFAULT 'pending';" ;;
        ned_source) db_exec "ALTER TABLE targets ADD COLUMN ned_source TEXT NOT NULL DEFAULT '';" ;;
        ned_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN ned_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_ned_status ON targets(ned_status);"

  for c in simbad_main_id simbad_otype simbad_ra_deg simbad_dec_deg simbad_status simbad_source simbad_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        simbad_main_id) db_exec "ALTER TABLE targets ADD COLUMN simbad_main_id TEXT NOT NULL DEFAULT '';" ;;
        simbad_otype) db_exec "ALTER TABLE targets ADD COLUMN simbad_otype TEXT NOT NULL DEFAULT '';" ;;
        simbad_ra_deg) db_exec "ALTER TABLE targets ADD COLUMN simbad_ra_deg REAL;" ;;
        simbad_dec_deg) db_exec "ALTER TABLE targets ADD COLUMN simbad_dec_deg REAL;" ;;
        simbad_status) db_exec "ALTER TABLE targets ADD COLUMN simbad_status TEXT NOT NULL DEFAULT 'pending';" ;;
        simbad_source) db_exec "ALTER TABLE targets ADD COLUMN simbad_source TEXT NOT NULL DEFAULT '';" ;;
        simbad_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN simbad_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_simbad_status ON targets(simbad_status);"

  for c in nasa_image_url nasa_thumb_url nasa_title nasa_nasa_id nasa_status nasa_source nasa_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        nasa_image_url) db_exec "ALTER TABLE targets ADD COLUMN nasa_image_url TEXT NOT NULL DEFAULT '';" ;;
        nasa_thumb_url) db_exec "ALTER TABLE targets ADD COLUMN nasa_thumb_url TEXT NOT NULL DEFAULT '';" ;;
        nasa_title) db_exec "ALTER TABLE targets ADD COLUMN nasa_title TEXT NOT NULL DEFAULT '';" ;;
        nasa_nasa_id) db_exec "ALTER TABLE targets ADD COLUMN nasa_nasa_id TEXT NOT NULL DEFAULT '';" ;;
        nasa_status) db_exec "ALTER TABLE targets ADD COLUMN nasa_status TEXT NOT NULL DEFAULT 'pending';" ;;
        nasa_source) db_exec "ALTER TABLE targets ADD COLUMN nasa_source TEXT NOT NULL DEFAULT '';" ;;
        nasa_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN nasa_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_nasa_status ON targets(nasa_status);"

  for c in distance_source distance_ref distance_ly identity_method identity_confidence coord_match_sep_arcsec constellation; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        distance_source) db_exec "ALTER TABLE targets ADD COLUMN distance_source TEXT NOT NULL DEFAULT '';" ;;
        distance_ref) db_exec "ALTER TABLE targets ADD COLUMN distance_ref TEXT NOT NULL DEFAULT '';" ;;
        distance_ly) db_exec "ALTER TABLE targets ADD COLUMN distance_ly REAL;" ;;
        identity_method) db_exec "ALTER TABLE targets ADD COLUMN identity_method TEXT NOT NULL DEFAULT '';" ;;
        identity_confidence) db_exec "ALTER TABLE targets ADD COLUMN identity_confidence REAL;" ;;
        coord_match_sep_arcsec) db_exec "ALTER TABLE targets ADD COLUMN coord_match_sep_arcsec REAL;" ;;
        constellation) db_exec "ALTER TABLE targets ADD COLUMN constellation TEXT NOT NULL DEFAULT '';" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_constellation ON targets(constellation);"



  for c in final_name final_objtype final_ra_deg final_dec_deg final_distance_value final_distance_unit final_source_summary; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        final_name) db_exec "ALTER TABLE targets ADD COLUMN final_name TEXT NOT NULL DEFAULT '';" ;;
        final_objtype) db_exec "ALTER TABLE targets ADD COLUMN final_objtype TEXT NOT NULL DEFAULT '';" ;;
        final_ra_deg) db_exec "ALTER TABLE targets ADD COLUMN final_ra_deg REAL;" ;;
        final_dec_deg) db_exec "ALTER TABLE targets ADD COLUMN final_dec_deg REAL;" ;;
        final_distance_value) db_exec "ALTER TABLE targets ADD COLUMN final_distance_value REAL;" ;;
        final_distance_unit) db_exec "ALTER TABLE targets ADD COLUMN final_distance_unit TEXT NOT NULL DEFAULT '';" ;;
        final_source_summary) db_exec "ALTER TABLE targets ADD COLUMN final_source_summary TEXT NOT NULL DEFAULT '';" ;;
      esac
    fi
  done




  for c in object_type_label_de object_type_label_en distance_unit_label_de distance_unit_label_en; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        object_type_label_de) db_exec "ALTER TABLE targets ADD COLUMN object_type_label_de TEXT NOT NULL DEFAULT '';" ;;
        object_type_label_en) db_exec "ALTER TABLE targets ADD COLUMN object_type_label_en TEXT NOT NULL DEFAULT '';" ;;
        distance_unit_label_de) db_exec "ALTER TABLE targets ADD COLUMN distance_unit_label_de TEXT NOT NULL DEFAULT '';" ;;
        distance_unit_label_en) db_exec "ALTER TABLE targets ADD COLUMN distance_unit_label_en TEXT NOT NULL DEFAULT '';" ;;
      esac
    fi
  done



  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_category ON targets(category);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_capture_profiles_lookup ON capture_profiles(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_source_id ON sessions(source_id);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(category);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_filter_set ON sessions(filter_set);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_target_id ON sessions(target_id);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_sessions_capture_profile_id ON sessions(capture_profile_id);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_raw_files_source_id ON raw_files(source_id);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_raw_files_filter_set ON raw_files(filter_set);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_raw_files_status ON raw_files(file_status);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_raw_files_derivative_kind ON raw_files(derivative_kind);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_raw_files_bayerpat ON raw_files(header_bayerpat);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_cal_assets_source_id ON calibration_assets(source_id);"

  db_seed_device_sources
  db_seed_device_instances
}

db_get_source_id() {
  db_require
  sqlite3 "$DB_PATH" "SELECT id FROM device_sources WHERE source_key='$(db_escape "$1")' LIMIT 1;"
}

db_get_or_create_target() {
  local canonical_name="${1:-}"
  local display_name="${2:-$canonical_name}"
  local category="${3:-unknown}"

  [[ -n "$canonical_name" ]] || { printf ""; return 0; }

  db_require
  sqlite3 "$DB_PATH" "
    INSERT INTO targets (canonical_name, display_name, category, created_at, updated_at)
    VALUES ('$(db_escape "$canonical_name")', '$(db_escape "$display_name")', '$(db_escape "$category")', datetime('now'), datetime('now'))
    ON CONFLICT(canonical_name) DO UPDATE SET
      display_name=excluded.display_name,
      category=excluded.category,
      updated_at=datetime('now','localtime');
    SELECT id FROM targets WHERE canonical_name='$(db_escape "$canonical_name")' LIMIT 1;
  " | tail -n 1
}

db_get_or_create_capture_profile() {
  local source_id="${1:-1}"
  local camera="${2:-}"
  local exp_seconds="${3:-0}"
  local gain="${4:-0}"
  local binning="${5:-1}"
  local filter_set="${6:-unknown}"
  local is_dark_profile="${7:-0}"

  [[ -n "$exp_seconds" ]] || exp_seconds=0
  [[ -n "$gain" ]] || gain=0
  [[ -n "$binning" ]] || binning=1
  [[ -n "$filter_set" ]] || filter_set="unknown"

  db_require
  sqlite3 "$DB_PATH" "
    INSERT INTO capture_profiles (source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile, created_at, updated_at)
    VALUES (
      $(printf '%s' "$source_id"),
      '$(db_escape "$camera")',
      $(printf '%s' "$exp_seconds"),
      $(printf '%s' "$gain"),
      $(printf '%s' "$binning"),
      '$(db_escape "$filter_set")',
      $(printf '%s' "$is_dark_profile"),
      datetime('now'),
      datetime('now')
    )
    ON CONFLICT(source_id, camera, exp_seconds, gain, binning, filter_set, is_dark_profile) DO UPDATE SET
      updated_at=datetime('now','localtime');
    SELECT id
      FROM capture_profiles
     WHERE source_id=$(printf '%s' "$source_id")
       AND camera='$(db_escape "$camera")'
       AND exp_seconds=$(printf '%s' "$exp_seconds")
       AND gain=$(printf '%s' "$gain")
       AND binning=$(printf '%s' "$binning")
       AND filter_set='$(db_escape "$filter_set")'
       AND is_dark_profile=$(printf '%s' "$is_dark_profile")
     LIMIT 1;
  " | tail -n 1
}


db_find_best_dark_session() {
  local source_id="${1:-1}"
  local exp="${2:-}"
  local gain="${3:-}"
  local binning="${4:-1}"
  local temp_c="${5:-}"
  local limit="${6:-5}"

  [[ -n "$exp" ]] || return 0
  [[ -n "$gain" ]] || return 0
  [[ -n "$binning" ]] || binning=1
  [[ -n "$limit" ]] || limit=5

  db_require
  sqlite3 "$DB_PATH" "
    SELECT
      id || '|' ||
      raw_session_path || '|' ||
      COALESCE(temp_avg,'') || '|' ||
      COALESCE(frame_count,0) || '|' ||
      CASE
        WHEN '$(db_escape "$temp_c")' = '' OR temp_avg IS NULL THEN 999999
        ELSE ABS(temp_avg - CAST('$(db_escape "$temp_c")' AS REAL))
      END AS temp_delta
    FROM sessions
    WHERE source_id=$(printf '%s' "$source_id")
      AND session_type='dark_raw_session'
      AND status='indexed'
      AND exp=$(printf '%s' "$exp")
      AND gain=$(printf '%s' "$gain")
      AND binning=$(printf '%s' "$binning")
    ORDER BY
      CASE
        WHEN '$(db_escape "$temp_c")' = '' OR temp_avg IS NULL THEN 999999
        ELSE ABS(temp_avg - CAST('$(db_escape "$temp_c")' AS REAL))
      END ASC,
      frame_count DESC,
      session_datetime DESC
    LIMIT $(printf '%s' "$limit");
  "
}

db_find_best_cal_dark() {
  local source_id="${1:-1}"
  local exp="${2:-}"
  local gain="${3:-}"
  local binning="${4:-1}"
  local temp_c="${5:-}"
  local limit="${6:-5}"

  [[ -n "$exp" ]] || return 0
  [[ -n "$gain" ]] || return 0
  [[ -n "$binning" ]] || binning=1
  [[ -n "$limit" ]] || limit=5

  db_require
  sqlite3 "$DB_PATH" "
    SELECT
      id || '|' ||
      abs_path || '|' ||
      COALESCE(temp_c,'') || '|' ||
      COALESCE(stack_count,0) || '|' ||
      CASE
        WHEN '$(db_escape "$temp_c")' = '' OR temp_c IS NULL THEN 999999
        ELSE ABS(temp_c - CAST('$(db_escape "$temp_c")' AS REAL))
      END AS temp_delta
    FROM calibration_assets
    WHERE source_id=$(printf '%s' "$source_id")
      AND asset_type='dark'
      AND exp=$(printf '%s' "$exp")
      AND gain=$(printf '%s' "$gain")
      AND binning=$(printf '%s' "$binning")
      AND is_current=1
    ORDER BY
      CASE
        WHEN '$(db_escape "$temp_c")' = '' OR temp_c IS NULL THEN 999999
        ELSE ABS(temp_c - CAST('$(db_escape "$temp_c")' AS REAL))
      END ASC,
      stack_count DESC,
      last_seen_at DESC
    LIMIT $(printf '%s' "$limit");
  "
}


db_job_start() {
  local job_name="$1" source="${2:-unknown}" note="${3:-}"
  db_require
  sqlite3 "$DB_PATH" \
    "INSERT INTO job_runs (job_name,status,source,note,started_at)
     VALUES ('$(db_escape "$job_name")','running','$(db_escape "$source")','$(db_escape "$note")',datetime('now','localtime'));
     SELECT last_insert_rowid();"
}

db_job_finish() {
  db_require
  sqlite3 "$DB_PATH" \
    "UPDATE job_runs
        SET status='$(db_escape "$2")',
            note='$(db_escape "${3:-}")',
            finished_at=datetime('now','localtime')
      WHERE id=$(printf '%s' "$1");"
}

db_set_state() {
  db_require
  sqlite3 "$DB_PATH" \
    "INSERT INTO app_state (key,value,updated_at)
     VALUES ('$(db_escape "$1")','$(db_escape "$2")',datetime('now','localtime'))
     ON CONFLICT(key) DO UPDATE SET
       value=excluded.value,
       updated_at=datetime('now','localtime');"
}

db_print_recent_runs_json() {
  db_require
  sqlite3 -json "$DB_PATH" \
    "SELECT id, job_name, status, started_at, finished_at, source, note
       FROM job_runs
      ORDER BY id DESC
      LIMIT 15;"
}
