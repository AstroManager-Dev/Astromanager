#!/usr/bin/env bash
set -euo pipefail

platesolve_extract_solution_data() {
  local wcs_path="${1:-}"
  local helper="${PLATESOLVE_WCSINFO_HELPER:-/app/bin/astro_extract_wcsinfo.py}"

  [[ -n "$wcs_path" ]] || {
    echo "ERRno_wcs_path"
    return 1
  }

  [[ -f "$wcs_path" ]] || {
    echo "ERRmissing_wcs$wcs_path"
    return 1
  }

  [[ -x "$helper" || -f "$helper" ]] || {
    echo "ERRmissing_helper$helper"
    return 1
  }

  python3 "$helper" "$wcs_path"
}

platesolve_apply_solution_to_session() {
  local session_key="${1:-}"
  local wcs_path="${2:-}"
  local result

  [[ -n "$session_key" ]] || {
    log "plate solve: missing session_key for apply_solution"
    return 1
  }

  result="$(platesolve_extract_solution_data "$wcs_path" 2>>"$LOG" || true)"

  if [[ -z "$result" ]]; then
    log "plate solve: empty extractor result: $wcs_path"
    return 1
  fi

  if [[ "${result%%$'\t'*}" != "OK" ]]; then
    log "plate solve: extractor failed: $result"
    return 1
  fi

  local ra dec fovx fovy pixscale rot engine msg
  ra="$(echo "$result"   | awk -F'\t' '{print $2}')"
  dec="$(echo "$result"  | awk -F'\t' '{print $3}')"
  fovx="$(echo "$result" | awk -F'\t' '{print $4}')"
  fovy="$(echo "$result" | awk -F'\t' '{print $5}')"
  pixscale="$(echo "$result" | awk -F'\t' '{print $6}')"
  rot="$(echo "$result"  | awk -F'\t' '{print $7}')"
  engine="$(echo "$result" | awk -F'\t' '{print $8}')"
  msg="$(echo "$result"  | awk -F'\t' '{print $9}')"

  sqlite3 "$DB_PATH" "
    UPDATE sessions
       SET platesolve_status='solved',
           platesolve_last_at=datetime('now'),
           solve_ra_deg=$(sql_num_or_null "$ra"),
           solve_dec_deg=$(sql_num_or_null "$dec"),
           solve_fov_x_deg=$(sql_num_or_null "$fovx"),
           solve_fov_y_deg=$(sql_num_or_null "$fovy"),
           solve_rotation_deg=$(sql_num_or_null "$rot"),
           solve_engine=$(sql_text_or_null "$engine"),
           solve_message=$(sql_text_or_null "$msg"),
           solve_pass='helper-wcsinfo'
     WHERE session_key=$(db_escape "$session_key");
  " >>"$LOG" 2>&1

  log "plate solve: solved: session=${session_key} ra=${ra} dec=${dec} fov=${fovx}x${fovy} rot=${rot} engine=${engine}"
  return 0
}

sql_num_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf "NULL"
  else
    printf "%s" "$v"
  fi
}

sql_text_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf "NULL"
  else
    printf "'%s'" "$(printf "%s" "$v" | sed "s/'/''/g")"
  fi
}
