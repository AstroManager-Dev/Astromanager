#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local base="${RAW_ROOT%/}/Astronomy"
  local state_root="${STATE_DIR_ARG%/}/index_sessions/light_sessions"

  session_signature() {
    local dir="$1"

    find "$dir" -maxdepth 1 -type f \
      \( -name '*.fits' -o -name '*.fit' -o -name '*.fts' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.tif' -o -name '*.tiff' -o -name '*.json' -o -name 'Thumbnail*' \) \
      -printf '%f|%s|%T@\n' | LC_ALL=C sort | sha1sum | awk '{print $1}'
  }

  session_state_file() {
    local dir="$1"
    local digest
    digest="$(printf '%s' "$dir" | sha1sum | awk '{print $1}')"
    printf '%s/%s.state\n' "$state_root" "$digest"
  }

  session_should_skip() {
    local dir="$1"
    local sig="$2"
    local state_file="$3"
    local old_sig=""

    [[ "${FULL_SCAN:-0}" -eq 1 ]] && return 1
    [[ "${DRY_RUN:-0}" -eq 1 ]] && return 1
    [[ -f "$state_file" ]] || return 1

    old_sig="$(sed -n '1p' "$state_file" 2>/dev/null || true)"
    [[ -n "$old_sig" && "$old_sig" == "$sig" ]]
  }

  session_write_state() {
    local state_file="$1"
    local sig="$2"
    local dir="$3"
    local ts
    ts="$(date +'%F %T')"
    mkdir -p "$(dirname "$state_file")"
    {
      printf '%s\n' "$sig"
      printf '%s\n' "$ts"
      printf '%s\n' "$dir"
    } > "$state_file"
  }

  [[ -d "$base" ]] || { log "scan light sessions: missing: $base"; return 0; }
  mkdir -p "$state_root"

  log "scan light sessions: $base"

  while IFS= read -r -d '' dir; do
    local name parsed target exp gain session_ts session_type category status
    local binning="1" frame_count=0 total_bytes=0 session_key filter_set="unknown"
    local temp_values="" temp_min="" temp_max="" temp_avg=""
    local session_header_object="" session_header_ra="" session_header_dec=""
    local session_header_exptime="" session_header_gain="" session_header_filter=""
    local has_fits=0 has_dwarf_stack=0 has_dwarf_preview=0 has_dwarf_metadata=0
    local target_id="" capture_profile_id=""
    local dir_sig="" state_file=""

    name="$(basename "$dir")"
    parsed="$(classify_light_session_name "$name")" || {
      log "scan light sessions: skip unparsed dir: $dir"
      continue
    }

    dir_sig="$(session_signature "$dir")"
    state_file="$(session_state_file "$dir")"

    if session_should_skip "$dir" "$dir_sig" "$state_file"; then
      sessions_skipped_unchanged=$((sessions_skipped_unchanged + 1))
      log "scan light sessions: skip unchanged: $dir"
      continue
    fi

    IFS='|' read -r target exp gain session_ts session_type category status <<< "$parsed"
    filter_set="$(detect_filter_set "$name" "$dir" "")"

    while IFS= read -r -d '' f; do
      local rel parent_dir file_name size_bytes mtime_epoch sha256
      local file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated
      local header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs
      local header_bayerpat tail2 header_xbayroff header_ybayroff is_color_sensor debayer_required
      local temp_c="" camera="cam_0" source_subtype meta_source

      rel="${f#${RAW_ROOT%/}/}"
      parent_dir="$(dirname "$f")"
      file_name="$(basename "$f")"

      IFS='|' read -r meta_source size_bytes mtime_epoch sha256 file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat tail2 <<< "$(get_file_meta "$f" "$dir" "$file_name" "$filter_set")"

      if [[ "$meta_source" == "cached" ]]; then
        files_reused=$((files_reused + 1))
      else
        files_hashed=$((files_hashed + 1))
      fi

      IFS='|' read -r header_xbayroff header_ybayroff is_color_sensor debayer_required <<< "$tail2"
      source_subtype="$derivative_kind"

      is_fits_file "$file_name" && has_fits=1
      [[ "$derivative_kind" == "dwarf_internal_stack" || "$derivative_kind" == "dwarf_stacked_fits" ]] && has_dwarf_stack=1
      [[ "$derivative_kind" == "dwarf_preview" ]] && has_dwarf_preview=1
      [[ "$derivative_kind" == "dwarf_metadata" ]] && has_dwarf_metadata=1
      [[ "$derivative_kind" == "other" ]] && continue

      if [[ "$file_name" =~ _([0-9]+)C\.fits$ ]] && [[ "$source_subtype" == "light_raw_frame" ]]; then
        temp_c="${BASH_REMATCH[1]}"
        temp_values+="${temp_values:+,}${temp_c}"
      fi

      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_object" && -n "${header_object:-}" ]] && session_header_object="$header_object"
      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_ra" && -n "${header_ra:-}" ]] && session_header_ra="$header_ra"
      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_dec" && -n "${header_dec:-}" ]] && session_header_dec="$header_dec"
      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_exptime" && -n "${header_exptime:-}" ]] && session_header_exptime="$header_exptime"
      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_gain" && -n "${header_gain:-}" ]] && session_header_gain="$header_gain"
      [[ "$source_subtype" == "light_raw_frame" && -z "$session_header_filter" && -n "${header_filter:-}" ]] && session_header_filter="$header_filter"

      upsert_raw_file \
        "astronomy_session" \
        "$source_subtype" \
        "$f" \
        "$rel" \
        "$parent_dir" \
        "$file_name" \
        "$size_bytes" \
        "$mtime_epoch" \
        "$sha256" \
        "" \
        "$file_filter" \
        "$file_status" \
        "$file_status_note" \
        "$derivative_kind" \
        "$is_session_input" \
        "$is_dwarf_generated" \
        "$header_object" \
        "$header_ra" \
        "$header_dec" \
        "$header_exptime" \
        "$header_gain" \
        "$header_filter" \
        "$header_date_obs" \
        "$header_bayerpat" \
        "$header_xbayroff" \
        "$header_ybayroff" \
        "$is_color_sensor" \
        "$debayer_required" \
        "$exp" \
        "$gain" \
        "$temp_c" \
        "$binning" \
        "$camera"

      if [[ "$source_subtype" == "light_raw_frame" ]]; then
        frame_count=$((frame_count + 1))
        total_bytes=$((total_bytes + size_bytes))
      fi

      files_indexed=$((files_indexed + 1))
      progress_maybe_log
    done < <(find "$dir" -maxdepth 1 -type f \( -name '*.fits' -o -name '*.fit' -o -name '*.fts' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.tif' -o -name '*.tiff' -o -name '*.json' -o -name 'Thumbnail*' \) -print0 | sort -z)

    (( has_fits == 1 )) || {
      log "scan light sessions: skip no-fits dir: $dir"
      continue
    }

    IFS='|' read -r target exp gain category status filter_set <<< "$(resolve_light_session_from_header "$target" "$exp" "$gain" "$category" "$status" "$filter_set" "$session_header_object" "$session_header_ra" "$session_header_dec" "$session_header_exptime" "$session_header_gain" "$session_header_filter")"

    session_key="$(stable_session_key "$dir")"
    IFS='|' read -r temp_min temp_max temp_avg <<< "$(compute_temp_stats "$temp_values")"
    capture_profile_id="$(db_get_or_create_capture_profile "$SOURCE_ID" "cam_0" "$exp" "$gain" "$binning" "$filter_set" 0)"

    if [[ -n "$target" && "$target" != "UNKNOWN" ]]; then
      target_id="$(db_get_or_create_target "$target" "$target" "$category")"
    fi

    upsert_session \
      "$session_key" \
      "$session_type" \
      "$category" \
      "$dir" \
      "$target" \
      "$filter_set" \
      "$exp" \
      "$gain" \
      "$binning" \
      "$session_ts" \
      "$status" \
      "$frame_count" \
      "$total_bytes" \
      "$temp_min" \
      "$temp_max" \
      "$temp_avg" \
      "$has_dwarf_stack" \
      "$has_dwarf_preview" \
      "$has_dwarf_metadata" \
      "$target_id" \
      "$capture_profile_id"

    sqlite3 "$DB_PATH" "UPDATE raw_files SET session_key='$(db_escape "$session_key")' WHERE source_id=$(sql_num_or_null "$SOURCE_ID") AND parent_dir='$(db_escape "$dir")';"

    session_write_state "$state_file" "$dir_sig" "$dir"
    sessions_indexed=$((sessions_indexed + 1))
  done < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name 'DWARF_RAW_TELE*' -print0 | sort -z)
}
