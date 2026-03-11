#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local base="${RAW_ROOT%/}/Astronomy"
  local platesolve_lib="/app/workflows/index/lib/platesolve_common.sh"

  [[ -f "$platesolve_lib" ]] || die "missing platesolve helper: $platesolve_lib"
  source "$platesolve_lib"

  [[ -d "$base" ]] || { log "plate solve: missing: $base"; return 0; }

  log "plate solve: $base"

  while IFS= read -r -d '' dir; do
    local name parsed target exp gain session_ts session_type category status
    local session_key filter_set dir_sig state_file ref_file result
    local ps_status ra dec fovx fovy rotation engine message pass_name
    local hint_ra="" hint_dec=""

    name="$(basename "$dir")"
    parsed="$(classify_light_session_name "$name")" || {
      log "plate solve: skip unparsed dir: $dir"
      continue
    }

    IFS='|' read -r target exp gain session_ts session_type category status <<< "$parsed"
    filter_set="$(detect_filter_set "$name" "$dir" "")"
    session_key="$(stable_session_key "$dir")"

    if platesolve_is_excluded_category "$target" "$category"; then
      log "plate solve: skip category: $dir"
      platesolve_update_session "$session_key" "not_applicable" "" "" "" "" "" "" "" "excluded category" ""
      continue
    fi

    if platesolve_should_skip_exposure "$exp"; then
      log "plate solve: skip exposure: $dir"
      platesolve_update_session "$session_key" "skipped_exposure" "" "" "" "" "" "" "" "exposure below deep-sky threshold" ""
      continue
    fi

    dir_sig="$(platesolve_session_signature "$dir")"
    state_file="$(platesolve_state_file "$dir")"

    if platesolve_should_skip "$dir_sig" "$state_file"; then
      log "plate solve: skip unchanged: $dir"
      continue
    fi

    if ! ref_file="$(platesolve_pick_reference_file "$dir" "$filter_set")"; then
      log "plate solve: skip quality: $dir"
      platesolve_update_session "$session_key" "skipped_quality" "" "" "" "" "" "" "" "no suitable ok light_raw_frame found" ""
      platesolve_write_state "$state_file" "$dir_sig" "$dir"
      continue
    fi

    IFS='|' read -r hint_ra hint_dec <<< "$(platesolve_extract_hint_from_file "$ref_file" "$dir")"

    log "plate solve: candidate: $dir"
    log "plate solve: using reference: $ref_file"

    if platesolve_is_valid_coord_pair "$hint_ra" "$hint_dec"; then
      log "plate solve: using hint: ra=$hint_ra dec=$hint_dec radius_fast=${PLATESOLVE_HINT_RADIUS_FAST_DEG:-8} radius_wide=${PLATESOLVE_HINT_RADIUS_WIDE_DEG:-15}"
    else
      log "plate solve: using hint: none"
      hint_ra=""
      hint_dec=""
    fi

    result="$(platesolve_run_solver "$ref_file" "$session_key" "$hint_ra" "$hint_dec")"
    IFS='|' read -r ps_status ra dec fovx fovy rotation engine message pass_name <<< "$result"

    case "$ps_status" in
      solved)
        log "plate solve: solved: $dir -> ra=$ra dec=$dec pass=$pass_name"
        platesolve_update_session "$session_key" "solved" "$ref_file" "$ra" "$dec" "$fovx" "$fovy" "$rotation" "$engine" "$message" "$pass_name"
        ;;
      solver_unavailable)
        log "plate solve: solver unavailable: $dir pass=$pass_name"
        platesolve_update_session "$session_key" "solver_unavailable" "$ref_file" "" "" "" "" "" "$engine" "$message" "$pass_name"
        ;;
      unsolved)
        log "plate solve: unsolved: $dir pass=$pass_name"
        platesolve_update_session "$session_key" "unsolved" "$ref_file" "" "" "" "" "" "$engine" "$message" "$pass_name"
        ;;
      failed|*)
        log "plate solve: failed: $dir pass=$pass_name"
        platesolve_update_session "$session_key" "failed" "$ref_file" "" "" "" "" "" "$engine" "$message" "$pass_name"
        ;;
    esac

    platesolve_write_state "$state_file" "$dir_sig" "$dir"
  done < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name 'DWARF_RAW_TELE*' -print0 | sort -z)
}
