#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local base="${RAW_ROOT%/}/Astronomy/DWARF_DARK"
  local state_root="${STATE_DIR_ARG%/}/index_sessions/dwarf_dark"

  session_signature() {
    local dir="$1"
    find "$dir" -type f -name '*.fits' -printf '%P|%s|%T@\n' | LC_ALL=C sort | sha1sum | awk '{print $1}'
  }

  session_state_file() {
    local dir="$1"
    local digest
    digest="$(printf '%s' "$dir" | sha1sum | awk '{print $1}')"
    printf '%s/%s.state\n' "$state_root" "$digest"
  }

  session_should_skip() {
    local sig="$1"
    local state_file="$2"
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

  [[ -d "$base" ]] || { log "scan dwarf_dark: missing: $base"; return 0; }

  mkdir -p "$state_root"
  log "scan dwarf_dark: $base"

  while IFS= read -r -d '' dir; do
    local name exp="" gain="" binning="" session_ts="" session_key=""
    local frame_count=0 total_bytes=0 temp_values="" temp_min="" temp_max="" temp_avg=""
    local capture_profile_id
    local dir_sig="" state_file=""

    name="$(basename "$dir")"
    [[ "$name" =~ ^tele_exp_([0-9.]+)_gain_([0-9]+)_bin_([0-9]+)_(.+)$ ]] || {
      log "scan dwarf_dark: skip unparsed dir: $dir"
      continue
    }

    dir_sig="$(session_signature "$dir")"
    state_file="$(session_state_file "$dir")"

    if session_should_skip "$dir_sig" "$state_file"; then
      sessions_skipped_unchanged=$((sessions_skipped_unchanged + 1))
      log "scan dwarf_dark: skip unchanged: $dir"
      continue
    fi

    exp="${BASH_REMATCH[1]}"
    gain="${BASH_REMATCH[2]}"
    binning="${BASH_REMATCH[3]}"
    session_ts="${BASH_REMATCH[4]}"
    session_key="$(stable_session_key "$dir")"

    while IFS= read -r -d '' f; do
      local rel parent_dir file_name size_bytes mtime_epoch sha256
      local file_status file_status_note filter_set derivative_kind is_session_input is_dwarf_generated
      local header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs
      local header_bayerpat tail2 header_xbayroff header_ybayroff is_color_sensor debayer_required
      local temp_c="" camera="cam_0" meta_source

      rel="${f#${RAW_ROOT%/}/}"
      parent_dir="$(dirname "$f")"
      file_name="$(basename "$f")"

      IFS='|' read -r meta_source size_bytes mtime_epoch sha256 file_status file_status_note filter_set derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat tail2 <<< "$(get_file_meta "$f" "$dir" "$file_name" "unknown")"

      if [[ "$meta_source" == "cached" ]]; then
        files_reused=$((files_reused + 1))
      else
        files_hashed=$((files_hashed + 1))
      fi

      IFS='|' read -r header_xbayroff header_ybayroff is_color_sensor debayer_required <<< "$tail2"

      if [[ "$file_name" =~ _([0-9]+)C\.fits$ ]]; then
        temp_c="${BASH_REMATCH[1]}"
        temp_values+="${temp_values:+,}${temp_c}"
      fi

      [[ -n "${header_exptime:-}" ]] && exp="$header_exptime"
      [[ -n "${header_gain:-}" ]] && gain="$(printf '%.0f' "$header_gain" 2>/dev/null || printf '%s' "$gain")"

      upsert_raw_file \
        "dwarf_dark" \
        "dark_raw_frame" \
        "$f" \
        "$rel" \
        "$parent_dir" \
        "$file_name" \
        "$size_bytes" \
        "$mtime_epoch" \
        "$sha256" \
        "$session_key" \
        "$filter_set" \
        "$file_status" \
        "$file_status_note" \
        "$derivative_kind" \
        1 \
        0 \
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

      frame_count=$((frame_count + 1))
      total_bytes=$((total_bytes + size_bytes))
      files_indexed=$((files_indexed + 1))
      progress_maybe_log
    done < <(find "$dir" -type f -name '*.fits' -print0 | sort -z)

    IFS='|' read -r temp_min temp_max temp_avg <<< "$(compute_temp_stats "$temp_values")"
    capture_profile_id="$(db_get_or_create_capture_profile "$SOURCE_ID" "cam_0" "$exp" "$gain" "$binning" "unknown" 1)"

    upsert_session \
      "$session_key" \
      "dark_raw_session" \
      "calibration" \
      "$dir" \
      "DARK" \
      "unknown" \
      "$exp" \
      "$gain" \
      "$binning" \
      "$session_ts" \
      "indexed" \
      "$frame_count" \
      "$total_bytes" \
      "$temp_min" \
      "$temp_max" \
      "$temp_avg" \
      0 \
      0 \
      0 \
      "" \
      "$capture_profile_id"

    session_write_state "$state_file" "$dir_sig" "$dir"
    sessions_indexed=$((sessions_indexed + 1))
  done < <(find "$base" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
}
