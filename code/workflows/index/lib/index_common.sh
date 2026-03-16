#!/usr/bin/env bash
set -euo pipefail

sql_num_or_null() { [[ -z "${1:-}" ]] && printf "NULL" || printf "%s" "$1"; }
safe_stat_size() { stat -c '%s' "$1"; }
safe_stat_mtime() { stat -c '%Y' "$1"; }
file_hash() { sha256sum "$1" | awk '{print $1}'; }
is_fits_file() { [[ "$1" == *.fits || "$1" == *.fit || "$1" == *.fts ]]; }

detect_filter_set() {
  local text
  text="$(printf '%s %s %s\n' "${1:-}" "${2:-}" "${3:-}" | tr '[:upper:]' '[:lower:]')"
  case "$text" in
    *dualband*|*dual-band*|*dual_band*|*duoband*|*duo-band*|*duo_band*|*narrowband*|*narrow-band*|*narrow_band*)
      printf "DualBand"
      ;;
    *astro*)
      printf "Astro"
      ;;
    *vis*)
      printf "VIS"
      ;;
    *)
      printf "unknown"
      ;;
  esac
}

normalize_object_category() {
  local n
  n="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')"
  case "$n" in
    sun) printf "sun" ;;
    moon) printf "moon" ;;
    ""|unknown) printf "unknown" ;;
    *) printf "deepsky" ;;
  esac
}

header_probe() {
  if is_fits_file "$1"; then
    python3 "$FITS_HEADER_PROBE" "$1"
  else
    printf 'ok|||||||||||||'
  fi
}

progress_maybe_log() {
  if (( files_indexed > 0 && files_indexed % progress_every == 0 )); then
    log "progress: files_indexed=${files_indexed}, files_hashed=${files_hashed}, files_reused=${files_reused}, cal_assets_indexed=${cal_assets_indexed}, sessions_indexed=${sessions_indexed}"
  fi
}

db_cached_raw_meta() {
  local abs_path="$1"
  local size_bytes="$2"
  local mtime_epoch="$3"

  sqlite3 "$DB_PATH" "
    SELECT sha256, file_status, file_status_note, filter_set, derivative_kind,
           is_session_input, is_dwarf_generated, header_object, header_ra, header_dec,
           COALESCE(header_exptime,''), COALESCE(header_gain,''), header_filter, header_date_obs,
           header_bayerpat, COALESCE(header_xbayroff,''), COALESCE(header_ybayroff,''),
           is_color_sensor, debayer_required
      FROM raw_files
     WHERE source_id=$(sql_num_or_null "$SOURCE_ID")
       AND abs_path='$(db_escape "$abs_path")'
       AND size_bytes=$(sql_num_or_null "$size_bytes")
       AND mtime_epoch=$(sql_num_or_null "$mtime_epoch")
     LIMIT 1;
  "
}

assess_file_status() {
  local abs_path="$1"
  local size_bytes="$2"

  [[ -f "$abs_path" ]] || { printf 'defect\tmissing file'; return; }
  [[ "$size_bytes" -gt 0 ]] || { printf 'defect\tzero size'; return; }

  printf 'ok\t'
}

stable_session_key() {
  local raw_session_path="$1"
  local source_key="${SOURCE_KEY:-unknown_source}"
  local digest

  digest="$(printf '%s' "${source_key}|${raw_session_path}" | sha1sum | awk '{print $1}')"
  printf '%s|%s\n' "$source_key" "${digest:0:16}"
}

compute_temp_stats() {
  local values="$1"
  [[ -n "$values" ]] || { printf '||'; return; }

  awk -F',' '
    BEGIN { min=""; max=""; sum=0; n=0 }
    {
      for (i=1; i<=NF; i++) {
        if ($i != "") {
          v = $i + 0;
          if (min == "" || v < min) min = v;
          if (max == "" || v > max) max = v;
          sum += v;
          n++;
        }
      }
    }
    END {
      if (n == 0) print "||";
      else printf "%s|%s|%.3f\n", min, max, sum/n;
    }
  ' <<< "$values"
}

classify_session_file() {
  local file_name="$1"
  case "$file_name" in
    stacked-*.fits) printf 'dwarf_stacked_fits|0|1' ;;
    stacked_*.fits) printf 'dwarf_internal_stack|1|1' ;;
    stacked_*.png|stacked.jpg|stacked_thumbnail.jpg|img_reference.png|img_stacked_*.tif|img_stacked_*.png|Thumbnail*)
      printf 'dwarf_preview|0|1'
      ;;
    shotsInfo.json)
      printf 'dwarf_metadata|0|1'
      ;;
    *.fits|*.fit|*.fts)
      printf 'light_raw_frame|1|0'
      ;;
    *)
      printf 'other|0|0'
      ;;
  esac
}

upsert_session() {
  local session_key="$1"
  local session_type="$2"
  local category="$3"
  local raw_session_path="$4"
  local target="$5"
  local filter_set="$6"
  local exp="$7"
  local gain="$8"
  local binning="$9"
  local session_datetime="${10}"
  local status="${11}"
  local frame_count="${12}"
  local total_bytes="${13}"
  local temp_min="${14}"
  local temp_max="${15}"
  local temp_avg="${16}"
  local has_dwarf_stack="${17}"
  local has_dwarf_preview="${18}"
  local has_dwarf_metadata="${19}"
  local target_id="${20:-}"
  local capture_profile_id="${21:-}"

  [[ "$DRY_RUN" -eq 1 ]] && return 0

  sqlite3 "$DB_PATH" <<SQL
INSERT INTO sessions (
  source_id, target_id, capture_profile_id, session_key, session_type, category, raw_session_path, target, filter_set, exp, gain, binning,
  session_datetime, source_origin, status, frame_count, total_bytes, temp_min, temp_max, temp_avg,
  has_dwarf_stack, has_dwarf_preview, has_dwarf_metadata, first_seen_at, last_seen_at
) VALUES (
  $(sql_num_or_null "$SOURCE_ID"),
  $(sql_num_or_null "$target_id"),
  $(sql_num_or_null "$capture_profile_id"),
  '$(db_escape "$session_key")',
  '$(db_escape "$session_type")',
  '$(db_escape "$category")',
  '$(db_escape "$raw_session_path")',
  '$(db_escape "$target")',
  '$(db_escape "$filter_set")',
  $(sql_num_or_null "$exp"),
  $(sql_num_or_null "$gain"),
  $(sql_num_or_null "$binning"),
  '$(db_escape "$session_datetime")',
  'dwarf_sync',
  '$(db_escape "$status")',
  $(sql_num_or_null "$frame_count"),
  $(sql_num_or_null "$total_bytes"),
  $(sql_num_or_null "$temp_min"),
  $(sql_num_or_null "$temp_max"),
  $(sql_num_or_null "$temp_avg"),
  $(sql_num_or_null "$has_dwarf_stack"),
  $(sql_num_or_null "$has_dwarf_preview"),
  $(sql_num_or_null "$has_dwarf_metadata"),
  datetime('now'),
  datetime('now')
)
ON CONFLICT(raw_session_path) DO UPDATE SET
  source_id=excluded.source_id,
  target_id=excluded.target_id,
  capture_profile_id=excluded.capture_profile_id,
  session_key=excluded.session_key,
  session_type=excluded.session_type,
  category=excluded.category,
  target=excluded.target,
  filter_set=excluded.filter_set,
  exp=excluded.exp,
  gain=excluded.gain,
  binning=excluded.binning,
  session_datetime=excluded.session_datetime,
  status=excluded.status,
  frame_count=excluded.frame_count,
  total_bytes=excluded.total_bytes,
  temp_min=excluded.temp_min,
  temp_max=excluded.temp_max,
  temp_avg=excluded.temp_avg,
  has_dwarf_stack=excluded.has_dwarf_stack,
  has_dwarf_preview=excluded.has_dwarf_preview,
  has_dwarf_metadata=excluded.has_dwarf_metadata,
  last_seen_at=datetime('now');
SQL
}

upsert_raw_file() {
  local source_domain="$1"
  local source_subtype="$2"
  local abs_path="$3"
  local rel_path="$4"
  local parent_dir="$5"
  local file_name="$6"
  local size_bytes="$7"
  local mtime_epoch="$8"
  local sha256="$9"
  local session_key="${10:-}"
  local filter_set="${11:-unknown}"
  local file_status="${12:-ok}"
  local file_status_note="${13:-}"
  local derivative_kind="${14:-}"
  local is_session_input="${15:-0}"
  local is_dwarf_generated="${16:-0}"
  local header_object="${17:-}"
  local header_ra="${18:-}"
  local header_dec="${19:-}"
  local header_exptime="${20:-}"
  local header_gain="${21:-}"
  local header_filter="${22:-}"
  local header_date_obs="${23:-}"
  local header_bayerpat="${24:-}"
  local header_xbayroff="${25:-}"
  local header_ybayroff="${26:-}"
  local is_color_sensor="${27:-0}"
  local debayer_required="${28:-0}"
  local exp="${29:-}"
  local gain="${30:-}"
  local temp_c="${31:-}"
  local binning="${32:-}"
  local camera="${33:-}"

  [[ "$DRY_RUN" -eq 1 ]] && return 0

  sqlite3 "$DB_PATH" <<SQL
INSERT INTO raw_files (
  source_id, source_domain, source_subtype, abs_path, rel_path, parent_dir, file_name,
  size_bytes, mtime_epoch, sha256, session_key, filter_set, file_status, file_status_note,
  derivative_kind, is_session_input, is_dwarf_generated,
  header_object, header_ra, header_dec, header_exptime, header_gain, header_filter, header_date_obs,
  header_bayerpat, header_xbayroff, header_ybayroff, is_color_sensor, debayer_required,
  exp, gain, temp_c, binning, camera, first_seen_at, last_seen_at, is_current
) VALUES (
  $(sql_num_or_null "$SOURCE_ID"),
  '$(db_escape "$source_domain")',
  '$(db_escape "$source_subtype")',
  '$(db_escape "$abs_path")',
  '$(db_escape "$rel_path")',
  '$(db_escape "$parent_dir")',
  '$(db_escape "$file_name")',
  $(sql_num_or_null "$size_bytes"),
  $(sql_num_or_null "$mtime_epoch"),
  '$(db_escape "$sha256")',
  '$(db_escape "$session_key")',
  '$(db_escape "$filter_set")',
  '$(db_escape "$file_status")',
  '$(db_escape "$file_status_note")',
  '$(db_escape "$derivative_kind")',
  $(sql_num_or_null "$is_session_input"),
  $(sql_num_or_null "$is_dwarf_generated"),
  '$(db_escape "$header_object")',
  '$(db_escape "$header_ra")',
  '$(db_escape "$header_dec")',
  $(sql_num_or_null "$header_exptime"),
  $(sql_num_or_null "$header_gain"),
  '$(db_escape "$header_filter")',
  '$(db_escape "$header_date_obs")',
  '$(db_escape "$header_bayerpat")',
  $(sql_num_or_null "$header_xbayroff"),
  $(sql_num_or_null "$header_ybayroff"),
  $(sql_num_or_null "$is_color_sensor"),
  $(sql_num_or_null "$debayer_required"),
  $(sql_num_or_null "$exp"),
  $(sql_num_or_null "$gain"),
  $(sql_num_or_null "$temp_c"),
  $(sql_num_or_null "$binning"),
  '$(db_escape "$camera")',
  datetime('now'),
  datetime('now'),
  1
)
ON CONFLICT(abs_path) DO UPDATE SET
  source_id=excluded.source_id,
  source_domain=excluded.source_domain,
  source_subtype=excluded.source_subtype,
  rel_path=excluded.rel_path,
  parent_dir=excluded.parent_dir,
  file_name=excluded.file_name,
  size_bytes=excluded.size_bytes,
  mtime_epoch=excluded.mtime_epoch,
  sha256=excluded.sha256,
  session_key=excluded.session_key,
  filter_set=excluded.filter_set,
  file_status=excluded.file_status,
  file_status_note=excluded.file_status_note,
  derivative_kind=excluded.derivative_kind,
  is_session_input=excluded.is_session_input,
  is_dwarf_generated=excluded.is_dwarf_generated,
  header_object=excluded.header_object,
  header_ra=excluded.header_ra,
  header_dec=excluded.header_dec,
  header_exptime=excluded.header_exptime,
  header_gain=excluded.header_gain,
  header_filter=excluded.header_filter,
  header_date_obs=excluded.header_date_obs,
  header_bayerpat=excluded.header_bayerpat,
  header_xbayroff=excluded.header_xbayroff,
  header_ybayroff=excluded.header_ybayroff,
  is_color_sensor=excluded.is_color_sensor,
  debayer_required=excluded.debayer_required,
  exp=excluded.exp,
  gain=excluded.gain,
  temp_c=excluded.temp_c,
  binning=excluded.binning,
  camera=excluded.camera,
  last_seen_at=datetime('now'),
  is_current=1;
SQL
}

upsert_calibration_asset() {
  local asset_type="$1"
  local asset_origin="$2"
  local camera="$3"
  local abs_path="$4"
  local rel_path="$5"
  local size_bytes="$6"
  local mtime_epoch="$7"
  local sha256="$8"
  local exp="$9"
  local gain="${10}"
  local binning="${11}"
  local temp_c="${12}"
  local stack_count="${13}"
  local ir_index="${14}"

  [[ "$DRY_RUN" -eq 1 ]] && return 0

  sqlite3 "$DB_PATH" "
    INSERT INTO calibration_assets (
      source_id, asset_type, asset_origin, camera, abs_path, rel_path,
      size_bytes, mtime_epoch, sha256, exp, gain, binning, temp_c,
      stack_count, ir_index, first_seen_at, last_seen_at, is_current
    ) VALUES (
      $(sql_num_or_null "$SOURCE_ID"),
      '$(db_escape "$asset_type")',
      '$(db_escape "$asset_origin")',
      '$(db_escape "$camera")',
      '$(db_escape "$abs_path")',
      '$(db_escape "$rel_path")',
      $(sql_num_or_null "$size_bytes"),
      $(sql_num_or_null "$mtime_epoch"),
      '$(db_escape "$sha256")',
      $(sql_num_or_null "$exp"),
      $(sql_num_or_null "$gain"),
      $(sql_num_or_null "$binning"),
      $(sql_num_or_null "$temp_c"),
      $(sql_num_or_null "$stack_count"),
      $(sql_num_or_null "$ir_index"),
      datetime('now'),
      datetime('now'),
      1
    )
    ON CONFLICT(abs_path) DO UPDATE SET
      source_id=excluded.source_id,
      rel_path=excluded.rel_path,
      size_bytes=excluded.size_bytes,
      mtime_epoch=excluded.mtime_epoch,
      sha256=excluded.sha256,
      exp=excluded.exp,
      gain=excluded.gain,
      binning=excluded.binning,
      temp_c=excluded.temp_c,
      stack_count=excluded.stack_count,
      ir_index=excluded.ir_index,
      last_seen_at=datetime('now'),
      is_current=1;
  "
}

get_file_meta() {
  local abs_path="$1"
  local dir_hint="${2:-}"
  local file_hint="${3:-}"
  local default_filter="${4:-unknown}"

  local size_bytes mtime_epoch cached sha256 file_status file_status_note derivative_kind is_session_input is_dwarf_generated
  local header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs
  local header_bayerpat header_xbayroff header_ybayroff is_color_sensor debayer_required
  local filter_set probe_status probe_note meta_source

  size_bytes="$(safe_stat_size "$abs_path")"
  mtime_epoch="$(safe_stat_mtime "$abs_path")"
  IFS='|' read -r derivative_kind is_session_input is_dwarf_generated <<< "$(classify_session_file "$file_hint")"
  cached="$(db_cached_raw_meta "$abs_path" "$size_bytes" "$mtime_epoch" || true)"

  if [[ -n "$cached" ]]; then
    meta_source="cached"
    IFS='|' read -r sha256 file_status file_status_note filter_set derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat header_xbayroff header_ybayroff is_color_sensor debayer_required <<< "$cached"
    [[ -n "${filter_set:-}" ]] || filter_set="$default_filter"
  else
    meta_source="hashed"
    sha256="$(file_hash "$abs_path")"
    IFS=$'\t' read -r file_status file_status_note <<< "$(assess_file_status "$abs_path" "$size_bytes")"
    IFS='|' read -r probe_status probe_note header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat header_xbayroff header_ybayroff is_color_sensor debayer_required <<< "$(header_probe "$abs_path" || true)"
    if [[ "${probe_status:-}" != "ok" && -n "${probe_status:-}" ]]; then
      [[ "$file_status" == "ok" ]] && file_status="${probe_status:-badfit}"
      [[ -n "${probe_note:-}" ]] && file_status_note="${probe_note}"
    fi
    filter_set="$(detect_filter_set "${header_filter:-}" "$dir_hint" "$file_hint")"
    [[ "$filter_set" == "unknown" && -n "$default_filter" ]] && filter_set="$default_filter"
  fi

  printf '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n' \
    "$meta_source" "$size_bytes" "$mtime_epoch" "$sha256" "$file_status" "$file_status_note" "$filter_set" \
    "$derivative_kind" "$is_session_input" "$is_dwarf_generated" "${header_object:-}" "${header_ra:-}" "${header_dec:-}" \
    "${header_exptime:-}" "${header_gain:-}" "${header_filter:-}" "${header_date_obs:-}" "${header_bayerpat:-}" "${header_xbayroff:-}|${header_ybayroff:-}|${is_color_sensor:-0}|${debayer_required:-0}"
}

classify_light_session_name() {
  local name="$1"

  if [[ "$name" =~ ^DWARF_RAW_TELE_Sun_EXP_([0-9.]+)_GAIN_([0-9]+)_(.+)$ ]]; then
    printf 'Sun|%s|%s|%s|light_session|sun|indexed\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
  elif [[ "$name" =~ ^DWARF_RAW_TELE_Moon_EXP_([0-9.]+)_GAIN_([0-9]+)_(.+)$ ]]; then
    printf 'Moon|%s|%s|%s|light_session|moon|indexed\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
  elif [[ "$name" =~ ^DWARF_RAW_TELE_Unknown_EXP_([0-9.]+)_GAIN_([0-9]+)_(.+)$ ]]; then
    printf 'UNKNOWN|%s|%s|%s|light_session|deepsky|unsolved\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
  elif [[ "$name" =~ ^DWARF_RAW_TELE_EXP_([0-9.]+)_GAIN_([0-9]+)_(.+)$ ]]; then
    printf 'UNKNOWN|%s|%s|%s|light_session_unknown|unknown|review\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}"
  elif [[ "$name" =~ ^DWARF_RAW_TELE_(.+)_EXP_([0-9.]+)_GAIN_([0-9]+)_(.+)$ ]]; then
    printf '%s|%s|%s|%s|light_session|deepsky|indexed\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}"
  else
    return 1
  fi
}

resolve_light_session_from_header() {
  local target="$1"
  local exp="$2"
  local gain="$3"
  local category="$4"
  local status="$5"
  local filter_set="$6"
  local header_object="$7"
  local header_ra="$8"
  local header_dec="$9"
  local header_exptime="${10}"
  local header_gain="${11}"
  local header_filter="${12}"
  local hc=""

  [[ -n "${header_exptime:-}" ]] && exp="$header_exptime"
  [[ -n "${header_gain:-}" ]] && gain="$(printf '%.0f' "$header_gain" 2>/dev/null || printf '%s' "$gain")"
  [[ -n "${header_filter:-}" ]] && filter_set="$(detect_filter_set "$header_filter" "" "")"

  hc="$(normalize_object_category "$header_object")"
  if [[ "$hc" == "sun" ]]; then
    target="Sun"; category="sun"; status="indexed"
  elif [[ "$hc" == "moon" ]]; then
    target="Moon"; category="moon"; status="indexed"
  elif [[ -n "${header_object:-}" && "$header_object" != "UNKNOWN" && "$header_object" != "Unknown" ]]; then
    target="$header_object"; category="deepsky"; status="indexed"
  elif [[ -n "${header_ra:-}" && -n "${header_dec:-}" ]]; then
    target="UNKNOWN"; category="deepsky"; status="unsolved"
  fi

  printf '%s|%s|%s|%s|%s|%s\n' "$target" "$exp" "$gain" "$category" "$status" "$filter_set"
}
