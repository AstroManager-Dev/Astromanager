#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
source "$ROOT/lib/pipeline_env.sh"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/db.sh"
source "$ROOT/workflows/index/lib/index_common.sh"

STATE_DIR_ARG="${STATE_DIR:-$RUNTIME_ROOT}"
LOG_DIR_ARG="${LOG_DIR:-$LOG_ROOT}"
OK_FILE="/dev/null"
DRY_RUN=0
FULL_SCAN=0
WORKFLOW="${WORKFLOW:-all}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR_ARG="$2"; shift 2 ;;
    --log-dir) LOG_DIR_ARG="$2"; shift 2 ;;
    --ok-file) OK_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --full) FULL_SCAN=1; shift ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    *) echo "index: unknown arg: $1" >&2; exit 2 ;;
  esac
done

LOG="$(mklog "${LOG_DIR_ARG%/}/steps" "index_${WORKFLOW}")"
LOCK_FILE="${LOCK_DIR%/}/index_${WORKFLOW}.lock"
SOURCE_KEY="${SOURCE_KEY:-dwarflab_dwarf3}"
FITS_HEADER_PROBE="${FITS_HEADER_PROBE:-/app/bin/fits_header_probe.py}"
STEPS_DIR="$ROOT/workflows/index/steps"

mkdir -p "$STATE_DIR_ARG" "$LOG_DIR_ARG" "$(dirname "$LOCK_FILE")"

if ! acquire_lock "$LOCK_FILE" 8; then
  echo "index: lock busy: $LOCK_FILE" >&2
  exit 10
fi

log "index: start"
log "RAW_ROOT=$RAW_ROOT"
log "DB_PATH=$DB_PATH"
log "DRY_RUN=$DRY_RUN"
log "FULL_SCAN=$FULL_SCAN"
log "WORKFLOW=$WORKFLOW"
log "SOURCE_KEY=$SOURCE_KEY"
log "STEPS_DIR=$STEPS_DIR"
log "STATE_DIR_ARG=$STATE_DIR_ARG"

db_init "$ROOT"
SOURCE_ID="$(db_get_source_id "$SOURCE_KEY")"
[[ -n "${SOURCE_ID:-}" ]] || die "missing source_id for source_key=$SOURCE_KEY"
[[ -d "$STEPS_DIR" ]] || die "missing steps dir: $STEPS_DIR"

files_indexed=0
files_hashed=0
files_reused=0
cal_assets_indexed=0
sessions_indexed=0
sessions_skipped_unchanged=0
progress_every=100

run_step_file() {
  local step_file="$1"

  log "run step: $(basename "$step_file")"
  source "$step_file"

  declare -F step_run >/dev/null || die "step file has no step_run(): $step_file"
  step_run
  unset -f step_run
}

step_in_workflow() {
  local step_file="$1"
  local base num

  base="$(basename "$step_file")"
  num="${base%%_*}"

  [[ "$num" =~ ^[0-9]{4}$ ]] || return 1

  case "$WORKFLOW" in
    all)
      return 0
      ;;
    calibration)
      (( 10#$num >= 100 && 10#$num <= 299 ))
      return
      ;;
    sessions)
      (( 10#$num >= 300 && 10#$num <= 499 ))
      return
      ;;
    resolve)
      (( 10#$num >= 500 && 10#$num <= 1199 ))
      return
      ;;
    cleanup)
      (( 10#$num >= 1200 && 10#$num <= 1999 ))
      return
      ;;
    *)
      die "unknown workflow: $WORKFLOW"
      ;;
  esac
}

run_all_steps() {
  local found=0
  local step_file

  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    if step_in_workflow "$step_file"; then
      found=1
      if [[ "$DRY_RUN" -eq 1 ]]; then
        log "dry-run step: $(basename "$step_file")"
      else
        run_step_file "$step_file"
      fi
    fi
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)

  if [[ "$found" -ne 1 ]]; then
  if [[ "$WORKFLOW" == "cleanup" ]]; then
    log "no cleanup steps active in $STEPS_DIR for workflow=$WORKFLOW"
    return 0
  fi
  die "no matching step files found in $STEPS_DIR for workflow=$WORKFLOW"
fi
}

run_id="$(db_job_start "index_${WORKFLOW}" "workflow" "controller auto-runs sorted step files from workflows/index/steps")"
status="ok"
note=""

if ! run_all_steps; then
  status="error"
  note="step execution failed"
fi

if [[ "$status" == "ok" ]]; then
  note="workflow=${WORKFLOW}, source_id=${SOURCE_ID}, files_indexed=${files_indexed}, files_hashed=${files_hashed}, files_reused=${files_reused}, cal_assets_indexed=${cal_assets_indexed}, sessions_indexed=${sessions_indexed}, sessions_skipped_unchanged=${sessions_skipped_unchanged}, dry_run=${DRY_RUN}, full_scan=${FULL_SCAN}"
  db_set_state "last_index_status" "ok"
  db_set_state "last_index_note" "$note"
  db_set_state "last_index_at" "$(date +'%F %T')"
  db_job_finish "$run_id" "ok" "$note"
  log "index: success"
  log "$note"
  [[ "$OK_FILE" == "/dev/null" ]] || touch "$OK_FILE"
else
  db_set_state "last_index_status" "error"
  db_set_state "last_index_note" "$note"
  db_job_finish "$run_id" "error" "$note"
  log "index: failed: $note"
  exit 20
fi
