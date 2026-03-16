sql_num_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf 'NULL'
  else
    printf '%s' "$v"
  fi
}

sql_text_or_null() {
  local v="${1:-}"
  if [[ -z "$v" ]]; then
    printf 'NULL'
  else
    printf "'%s'" "$(printf "%s" "$v" | sed "s/'/''/g")"
  fi
}

step_run() {
  local py="/app/bin/astro_target_resolve.py"
  local upsert_py="/app/bin/upsert_session_target_candidates.py"
  local catalog="${OPENNGC_CSV_LOCAL:-/app/catalog/_db/openngc.csv}"
  local secondary_frac="${THRESH_NAME_SECONDARY_FRAC:-0.35}"
  local secondary_min="${THRESH_NAME_SECONDARY_MIN_ARCMIN:-8.0}"
  local max_candidates="${TARGET_RESOLVE_MAX_CANDIDATES:-25}"

  [[ -f "$py" ]] || die "missing helper: $py"
  [[ -f "$upsert_py" ]] || die "missing helper: $upsert_py"

  /app/bin/ensure_openngc_csv.sh
  [[ -f "$catalog" ]] || die "missing OpenNGC csv: $catalog"

  log "target resolve: start catalog=$catalog"

  sqlite3 -separator $'\t' "$DB_PATH" "
    SELECT session_key,
           COALESCE(target, ''),
           solve_ra_deg,
           solve_dec_deg,
           footprint_radius_deg
      FROM sessions
     WHERE platesolve_status='solved'
       AND solve_ra_deg IS NOT NULL
       AND solve_dec_deg IS NOT NULL
       AND footprint_radius_deg IS NOT NULL
       AND (target_final IS NULL OR ${FULL_SCAN:-0}=1)
     ORDER BY last_seen_at DESC;
  " | while IFS=$'\t' read -r session_key target_raw ra dec radius; do
    [[ -n "${session_key:-}" ]] || continue
    [[ -n "${ra:-}" && -n "${dec:-}" && -n "${radius:-}" ]] || continue

    local json
    if ! json="$(python3 "$py" "$catalog" "$ra" "$dec" "$radius" "$target_raw" "$secondary_frac" "$secondary_min" "$max_candidates" 2>>"$LOG")"; then
      log "target resolve: helper failed session=$session_key"
      continue
    fi

    local parsed
    if ! parsed="$(python3 - <<'PY' "$json"
import json, sys
d = json.loads(sys.argv[1])
vals = [
    d.get("target_final", ""),
    d.get("target_strategy", ""),
    d.get("field_object_count", ""),
    d.get("requested_target_found", ""),
    d.get("target_conflict_flag", ""),
    d.get("target_conflict_note", ""),
]
print("\t".join("" if v is None else str(v) for v in vals))
PY
)"; then
      log "target resolve: failed parsing helper json: session=$session_key"
      continue
    fi

    local target_final target_strategy field_count requested_found conflict_flag conflict_note
    IFS=$'\t' read -r target_final target_strategy field_count requested_found conflict_flag conflict_note <<< "$parsed"

    if ! python3 "$upsert_py" "$json" "$DB_PATH" "$session_key" 2>>"$LOG"; then
      log "target resolve: upsert helper failed session=$session_key"
      continue
    fi

    sqlite3 "$DB_PATH" "
      UPDATE sessions
         SET target_final=$(sql_text_or_null "$target_final"),
             target_final_source='platesolve_field_match',
             target_strategy=$(sql_text_or_null "$target_strategy"),
             field_object_count=$(sql_num_or_null "$field_count"),
             requested_target_found=$(sql_num_or_null "$requested_found"),
             target_conflict_flag=$(sql_num_or_null "$conflict_flag"),
             target_conflict_note=$(sql_text_or_null "$conflict_note")
       WHERE session_key='$(printf "%s" "$session_key" | sed "s/'/''/g")';
    "

    log "target resolve: session=$session_key target_final=$target_final strategy=$target_strategy count=$field_count"
  done
}
