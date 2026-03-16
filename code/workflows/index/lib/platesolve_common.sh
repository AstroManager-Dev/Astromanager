#!/usr/bin/env bash
set -euo pipefail

platesolve_state_file() {
  local dir="$1"
  local state_root="${STATE_DIR_ARG%/}/index_sessions/plate_solve"
  local digest
  digest="$(printf '%s' "$dir" | sha1sum | awk '{print $1}')"
  mkdir -p "$state_root"
  printf '%s/%s.state\n' "$state_root" "$digest"
}

platesolve_session_signature() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f \
    \( -name '*.fits' -o -name '*.fit' -o -name '*.fts' \) \
    -printf '%f|%s|%T@\n' | LC_ALL=C sort | sha1sum | awk '{print $1}'
}

platesolve_should_skip() {
  local sig="$1"
  local state_file="$2"
  local old_sig=""

  [[ "${FULL_SCAN:-0}" -eq 1 ]] && return 1
  [[ "${DRY_RUN:-0}" -eq 1 ]] && return 1
  [[ -f "$state_file" ]] || return 1

  old_sig="$(sed -n '1p' "$state_file" 2>/dev/null || true)"
  [[ -n "$old_sig" && "$old_sig" == "$sig" ]]
}

platesolve_write_state() {
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

platesolve_sql_text_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf 'NULL'
  else
    printf "'%s'" "$(db_escape "$v")"
  fi
}

platesolve_is_excluded_category() {
  local target="$1"
  local category="$2"

  case "${category,,}" in
    sun|moon|calibration|cali_frame|dwarf_dark) return 0 ;;
  esac

  case "${target,,}" in
    sun|moon|dark|bias|flat) return 0 ;;
  esac

  return 1
}

platesolve_should_skip_exposure() {
  local exp="${1:-}"
  awk -v e="${exp:-0}" 'BEGIN { exit !(e < 1.0) }'
}

platesolve_pick_reference_file() {
  local dir="$1"
  local filter_set="${2:-unknown}"
  local -a candidates=()
  local f file_name meta_source size_bytes mtime_epoch sha256
  local file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated
  local header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs
  local header_bayerpat tail2

  while IFS= read -r -d '' f; do
    file_name="$(basename "$f")"

    IFS='|' read -r meta_source size_bytes mtime_epoch sha256 file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat tail2 <<< "$(get_file_meta "$f" "$dir" "$file_name" "$filter_set")"

    [[ "$derivative_kind" == "light_raw_frame" ]] || continue
    [[ "$file_status" == "ok" ]] || continue
    candidates+=("$f")
  done < <(find "$dir" -maxdepth 1 -type f \( -name '*.fits' -o -name '*.fit' -o -name '*.fts' \) -print0 | sort -z)

  [[ "${#candidates[@]}" -gt 0 ]] || return 1

  local mid=$(( ${#candidates[@]} / 2 ))
  printf '%s\n' "${candidates[$mid]}"
}

platesolve_extract_hint_from_file() {
  local ref_file="$1"
  local dir="$2"
  local file_name
  local filter_set="unknown"
  local meta_source size_bytes mtime_epoch sha256
  local file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated
  local header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs
  local header_bayerpat tail2

  file_name="$(basename "$ref_file")"

  IFS='|' read -r meta_source size_bytes mtime_epoch sha256 file_status file_status_note file_filter derivative_kind is_session_input is_dwarf_generated header_object header_ra header_dec header_exptime header_gain header_filter header_date_obs header_bayerpat tail2 <<< "$(get_file_meta "$ref_file" "$dir" "$file_name" "$filter_set")"

  printf '%s|%s\n' "${header_ra:-}" "${header_dec:-}"
}

platesolve_is_valid_coord_pair() {
  local ra="${1:-}"
  local dec="${2:-}"

  [[ -n "$ra" && -n "$dec" ]] || return 1

  awk -v ra="$ra" -v dec="$dec" 'BEGIN {
    if (ra < 0 || ra > 360) exit 1;
    if (dec < -90 || dec > 90) exit 1;
    exit 0
  }'
}

platesolve_get_scale_hint() {
  local session_key="${1:-}"
  local dir="${2:-}"

  local scale_low="${PLATESOLVE_SCALE_LOW_ARCSECPERPIX:-2.0}"
  local scale_high="${PLATESOLVE_SCALE_HIGH_ARCSECPERPIX:-3.6}"

  printf '%s|%s\n' "$scale_low" "$scale_high"
}

platesolve_clear_workdir() {
  local work_dir="$1"
  rm -f \
    "${work_dir}/solved.flag" \
    "${work_dir}/solution.wcs" \
    "${work_dir}/solve-field.log" \
    "${work_dir}/solution.axy" \
    "${work_dir}/solution-indx.xyls" \
    "${work_dir}/solution-objs.png" \
    "${work_dir}/solution-ngc.png" \
    "${work_dir}/solution.corr" \
    "${work_dir}/solution.rdls" \
    "${work_dir}/solution.match" \
    "${work_dir}/solution.solved" \
    "${work_dir}/solution.new"
}

platesolve_extract_solution_with_helper() {
  local wcs_file="$1"
  local helper="${PLATESOLVE_WCSINFO_HELPER:-/app/bin/astro_extract_wcsinfo.py}"

  if [[ ! -f "$wcs_file" ]]; then
    printf 'ERR|||||||missing wcs file: %s\n' "$wcs_file"
    return 0
  fi

  if [[ ! -f "$helper" ]]; then
    printf 'ERR|||||||missing helper: %s\n' "$helper"
    return 0
  fi

  python3 "$helper" "$wcs_file" 2>>"$LOG" || true
}

platesolve_run_solver_pass() {
  local ref_file="$1"
  local session_key="$2"
  local pass_name="$3"
  local hint_ra="$4"
  local hint_dec="$5"
  local hint_radius="$6"
  local scale_low="$7"
  local scale_high="$8"
  local depth="$9"
  local objs="${10}"
  local downsample="${11}"
  local cpulimit="${12}"

  local work_root="${WORK_ROOT%/}/platesolve"
  local work_dir="${work_root%/}/${session_key}"
  local log_file="${work_dir}/solve-field.log"
  local wcs_file="${work_dir}/solution.wcs"

  mkdir -p "$work_dir"
  platesolve_clear_workdir "$work_dir"

  if ! command -v solve-field >/dev/null 2>&1; then
    printf 'solver_unavailable||||||||solve-field not found|%s\n' "$pass_name"
    return 0
  fi

  local -a solve_cmd=(
    timeout "$cpulimit"
    solve-field
    --overwrite
    --no-plots
    --dir "$work_dir"
    --scale-units arcsecperpix
    --scale-low "$scale_low"
    --scale-high "$scale_high"
    --new-fits none
    --solved "${work_dir}/solved.flag"
    --match none
    --rdls none
    --corr none
    --wcs "$wcs_file"
    --depth "$depth"
    --objs "$objs"
    --downsample "$downsample"
    --cpulimit "$cpulimit"
    --resort
  )

  if [[ -n "$hint_radius" ]] && platesolve_is_valid_coord_pair "$hint_ra" "$hint_dec"; then
    solve_cmd+=( --ra "$hint_ra" --dec "$hint_dec" --radius "$hint_radius" )
  fi

  solve_cmd+=( "$ref_file" )

  {
    echo "PASS_NAME=$pass_name"
    echo "REF_FILE=$ref_file"
    echo "HINT_RA=${hint_ra:-}"
    echo "HINT_DEC=${hint_dec:-}"
    echo "HINT_RADIUS=${hint_radius:-}"
    echo "SCALE_LOW=$scale_low"
    echo "SCALE_HIGH=$scale_high"
    echo "DEPTH=$depth"
    echo "OBJS=$objs"
    echo "DOWNSAMPLE=$downsample"
    echo "CPULIMIT=$cpulimit"
    echo "COMMAND=${solve_cmd[*]}"
    echo "-----"
  } > "$log_file"

  if ! "${solve_cmd[@]}" >>"$log_file" 2>&1; then
    printf 'failed||||||||solve-field failed or timed out|%s\n' "$pass_name"
    return 0
  fi

  [[ -f "$wcs_file" ]] || {
    printf 'unsolved||||||||no wcs output created|%s\n' "$pass_name"
    return 0
  }

  local helper_out
  helper_out="$(platesolve_extract_solution_with_helper "$wcs_file")"

  if [[ -z "$helper_out" ]]; then
    printf 'unsolved||||||||helper returned empty output|%s\n' "$pass_name"
    return 0
  fi

  if [[ "${helper_out%%$'\t'*}" != "OK" ]]; then
    printf 'unsolved||||||||%s|%s\n' "$helper_out" "$pass_name"
    return 0
  fi

  local ra dec fieldw fieldh pixscale rotation engine message
  ra="$(echo "$helper_out"       | awk -F'\t' '{print $2}')"
  dec="$(echo "$helper_out"      | awk -F'\t' '{print $3}')"
  fieldw="$(echo "$helper_out"   | awk -F'\t' '{print $4}')"
  fieldh="$(echo "$helper_out"   | awk -F'\t' '{print $5}')"
  pixscale="$(echo "$helper_out" | awk -F'\t' '{print $6}')"
  rotation="$(echo "$helper_out" | awk -F'\t' '{print $7}')"
  engine="$(echo "$helper_out"   | awk -F'\t' '{print $8}')"
  message="$(echo "$helper_out"  | awk -F'\t' '{print $9}')"

  if [[ -z "${ra:-}" || -z "${dec:-}" ]]; then
    printf 'unsolved||||||||helper returned no center coordinates|%s\n' "$pass_name"
    return 0
  fi

  [[ -n "${engine:-}" ]] || engine="astrometry.net solve-field"
  [[ -n "${message:-}" ]] || message="ok pixscale=${pixscale:-}"

  printf 'solved|%s|%s|%s|%s|%s|%s|%s|%s\n' \
    "$ra" "$dec" "${fieldw:-}" "${fieldh:-}" "${rotation:-}" "$engine" "$message" "$pass_name"
}

platesolve_run_solver() {
  local ref_file="$1"
  local session_key="$2"
  local hint_ra="${3:-}"
  local hint_dec="${4:-}"

  local scale_low scale_high
  IFS='|' read -r scale_low scale_high <<< "$(platesolve_get_scale_hint "$session_key" "$(dirname "$ref_file")")"

  local fast_radius="${PLATESOLVE_HINT_RADIUS_FAST_DEG:-8}"
  local wide_radius="${PLATESOLVE_HINT_RADIUS_WIDE_DEG:-15}"

  local result status ra dec fovx fovy rotation engine message pass_name

  if platesolve_is_valid_coord_pair "$hint_ra" "$hint_dec"; then
    result="$(platesolve_run_solver_pass \
      "$ref_file" "$session_key" \
      "local-fast" \
      "$hint_ra" "$hint_dec" "$fast_radius" \
      "$scale_low" "$scale_high" \
      "11-30" "100" "2" "120")"
    IFS='|' read -r status ra dec fovx fovy rotation engine message pass_name <<< "$result"
    [[ "$status" == "solved" ]] && { printf '%s\n' "$result"; return 0; }

    result="$(platesolve_run_solver_pass \
      "$ref_file" "$session_key" \
      "local-wide" \
      "$hint_ra" "$hint_dec" "$wide_radius" \
      "$scale_low" "$scale_high" \
      "1-50" "150" "2" "180")"
    IFS='|' read -r status ra dec fovx fovy rotation engine message pass_name <<< "$result"
    [[ "$status" == "solved" ]] && { printf '%s\n' "$result"; return 0; }
  fi

  result="$(platesolve_run_solver_pass \
    "$ref_file" "$session_key" \
    "blind-fallback" \
    "" "" "" \
    "$scale_low" "$scale_high" \
    "1-50" "150" "2" "180")"
  printf '%s\n' "$result"
}

platesolve_update_session() {
  local session_key="$1"
  local status="$2"
  local ref_path="$3"
  local ra="$4"
  local dec="$5"
  local fovx="$6"
  local fovy="$7"
  local rotation="$8"
  local engine="$9"
  local message="${10}"
  local pass_name="${11:-}"

  local solve_status_sql="NULL"
  if [[ "$status" == "solved" ]]; then
    solve_status_sql="'solved'"
  fi

  sqlite3 "$DB_PATH" "
    UPDATE sessions
       SET platesolve_status='$(db_escape "$status")',
           platesolve_attempts=COALESCE(platesolve_attempts,0)+1,
           platesolve_last_at=datetime('now'),
           platesolve_reference_path=$(platesolve_sql_text_or_null "$ref_path"),
           solve_ra_deg=$(sql_num_or_null "$ra"),
           solve_dec_deg=$(sql_num_or_null "$dec"),
           solve_fov_x_deg=$(sql_num_or_null "$fovx"),
           solve_fov_y_deg=$(sql_num_or_null "$fovy"),
           solve_rotation_deg=$(sql_num_or_null "$rotation"),
           solve_engine=$(platesolve_sql_text_or_null "$engine"),
           solve_message=$(platesolve_sql_text_or_null "$message"),
           solve_pass=$(platesolve_sql_text_or_null "$pass_name"),
           solve_status=COALESCE($solve_status_sql, solve_status)
     WHERE session_key='$(db_escape "$session_key")';
  "
}
