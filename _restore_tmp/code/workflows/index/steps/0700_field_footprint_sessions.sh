#!/usr/bin/env bash
set -euo pipefail

sql_num_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf 'NULL'
  else
    printf '%s' "$v"
  fi
}

step_run() {
  local py="/app/bin/astro_field_footprint.py"
  [[ -f "$py" ]] || die "missing helper: $py"

  log "field footprint: start"

  sqlite3 --separator $'\t' "$DB_PATH" "
    SELECT session_key,
           platesolve_reference_path
      FROM sessions
     WHERE platesolve_status='solved'
       AND solve_ra_deg IS NOT NULL
       AND solve_dec_deg IS NOT NULL
       AND (corner_ul_ra_deg IS NULL OR ${FULL_SCAN:-0}=1)
     ORDER BY last_seen_at DESC;
  " | while IFS=$'\t' read -r session_key ref_path; do
    [[ -n "${session_key:-}" && -n "${ref_path:-}" ]] || continue

    local work_dir="${WORK_ROOT%/}/platesolve/${session_key}"
    local wcs_file="${work_dir}/solution.wcs"

    if [[ ! -f "$wcs_file" ]]; then
      log "field footprint: skip missing wcs: session=$session_key file=$wcs_file"
      continue
    fi

    if [[ ! -f "$ref_path" ]]; then
      log "field footprint: skip missing ref: session=$session_key file=$ref_path"
      continue
    fi

    local json
    if ! json="$(python3 "$py" "$wcs_file" "$ref_path" 2>>"$LOG")"; then
      log "field footprint: failed helper: session=$session_key"
      continue
    fi

    local parsed
    if ! parsed="$(python3 - <<'PY' "$json"
import json, sys

d = json.loads(sys.argv[1])

def out(v):
    if v is None:
        return ""
    return str(v)

fields = [
    d.get("center_ra_deg"),
    d.get("center_dec_deg"),
    d.get("fov_x_deg"),
    d.get("fov_y_deg"),
    d.get("footprint_radius_deg"),
    d.get("rotation_deg"),
    d.get("corner_ul_ra_deg"),
    d.get("corner_ul_dec_deg"),
    d.get("corner_ur_ra_deg"),
    d.get("corner_ur_dec_deg"),
    d.get("corner_lr_ra_deg"),
    d.get("corner_lr_dec_deg"),
    d.get("corner_ll_ra_deg"),
    d.get("corner_ll_dec_deg"),
]
print("\t".join(out(v) for v in fields))
PY
)"; then
      log "field footprint: failed parsing helper json: session=$session_key"
      continue
    fi

    local center_ra center_dec fovx fovy radius rot
    local ul_ra ul_dec ur_ra ur_dec lr_ra lr_dec ll_ra ll_dec

    IFS=$'\t' read -r \
      center_ra center_dec fovx fovy radius rot \
      ul_ra ul_dec ur_ra ur_dec lr_ra lr_dec ll_ra ll_dec <<< "$parsed"

    sqlite3 "$DB_PATH" "
      UPDATE sessions
         SET solve_ra_deg=$(sql_num_or_null "$center_ra"),
             solve_dec_deg=$(sql_num_or_null "$center_dec"),
             solve_fov_x_deg=$(sql_num_or_null "$fovx"),
             solve_fov_y_deg=$(sql_num_or_null "$fovy"),
             footprint_radius_deg=$(sql_num_or_null "$radius"),
             solve_rotation_deg=$(sql_num_or_null "$rot"),
             corner_ul_ra_deg=$(sql_num_or_null "$ul_ra"),
             corner_ul_dec_deg=$(sql_num_or_null "$ul_dec"),
             corner_ur_ra_deg=$(sql_num_or_null "$ur_ra"),
             corner_ur_dec_deg=$(sql_num_or_null "$ur_dec"),
             corner_lr_ra_deg=$(sql_num_or_null "$lr_ra"),
             corner_lr_dec_deg=$(sql_num_or_null "$lr_dec"),
             corner_ll_ra_deg=$(sql_num_or_null "$ll_ra"),
             corner_ll_dec_deg=$(sql_num_or_null "$ll_dec")
       WHERE session_key='$(db_escape "$session_key")';
    "

    log "field footprint: updated session=$session_key ra=$center_ra dec=$center_dec fov=${fovx}x${fovy}"
  done
}
