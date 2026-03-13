#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

ROOT="/app"
source "$ROOT/lib/pipeline_env.sh"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/db.sh"

RAW_SYNC_SOURCE_KEY="${RAW_SYNC_SOURCE_KEY:-dwarflab_dwarf3}"
RAW_SYNC_HOST="${RAW_SYNC_HOST:-192.168.2.163}"
RAW_SYNC_USER="${RAW_SYNC_USER:-anonymous}"
RAW_SYNC_PASS="${RAW_SYNC_PASS:-}"
RAW_SYNC_TIMEOUT="${RAW_SYNC_TIMEOUT:-15}"
RAW_SYNC_DRY_RUN="${RAW_SYNC_DRY_RUN:-0}"

STATE_DIR_ARG="${STATE_DIR:-$RUNTIME_ROOT}"
LOG_DIR_ARG="${LOG_DIR:-$LOG_ROOT}"
OK_FILE="/dev/null"
STEPS_DIR="$ROOT/workflows/raw/steps"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR_ARG="$2"; shift 2 ;;
    --log-dir) LOG_DIR_ARG="$2"; shift 2 ;;
    --ok-file) OK_FILE="$2"; shift 2 ;;
    --dry-run) RAW_SYNC_DRY_RUN=1; shift ;;
    *) echo "raw sync: unknown arg: $1" >&2; exit 2 ;;
  esac
done

LOG="$(mklog "${LOG_DIR_ARG%/}/steps" "raw_sync")"
LOCK_FILE="${LOCK_DIR%/}/raw_sync.lock"

mkdir -p "$STATE_DIR_ARG" "$LOG_DIR_ARG" "$(dirname "$LOCK_FILE")"

if ! acquire_lock "$LOCK_FILE" 8; then
  echo "raw sync: lock busy: $LOCK_FILE" >&2
  exit 10
fi

log "raw sync start source=$RAW_SYNC_SOURCE_KEY host=$RAW_SYNC_HOST dry_run=$RAW_SYNC_DRY_RUN"
log "ROOT=$ROOT"
log "DB_PATH=$DB_PATH"
log "RAW_ROOT=$RAW_ROOT"
log "STATE_DIR_ARG=$STATE_DIR_ARG"
log "LOG_DIR_ARG=$LOG_DIR_ARG"
log "STEPS_DIR=$STEPS_DIR"

db_init "$ROOT"
[[ -d "$STEPS_DIR" ]] || die "missing steps dir: $STEPS_DIR"

RUN_ID_TS="$(date +'%F_%H-%M-%S')"
RUN_DIR_PATH="${STATE_DIR_ARG%/}/run/raw_sync/${RUN_ID_TS}"
mkdir -p "$RUN_DIR_PATH"

export ROOT
export LOG
export DB_PATH
export RAW_ROOT
export RUN_DIR_PATH
export STATE_DIR_PATH="$STATE_DIR_ARG"
export LOG_DIR_PATH="$LOG_DIR_ARG"
export RAW_SYNC_SOURCE_KEY
export RAW_SYNC_HOST
export RAW_SYNC_USER
export RAW_SYNC_PASS
export RAW_SYNC_TIMEOUT
export RAW_SYNC_DRY_RUN

run_step_file() {
  local step_file="$1"

  log "run step=$(basename "$step_file")"

  if grep -qE '^[[:space:]]*step_run[[:space:]]*\(\)' "$step_file"; then
    source "$step_file"
    declare -F step_run >/dev/null || die "step file has no step_run(): $step_file"
    step_run
    unset -f step_run
  else
    bash "$step_file"
  fi
}

run_all_steps() {
  local found=0
  local step_file

  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    found=1
    if [[ "$RAW_SYNC_DRY_RUN" -eq 1 ]]; then
      case "$(basename "$step_file")" in
        0040_*|0060_*)
          log "dry-run step: $(basename "$step_file")"
          run_step_file "$step_file"
          ;;
        *)
          run_step_file "$step_file"
          ;;
      esac
    else
      run_step_file "$step_file"
    fi
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)

  [[ "$found" -eq 1 ]] || die "no matching step files found in $STEPS_DIR"
}

job_id="$(db_job_start "raw_sync" "workflow" "controller auto-runs sorted step files from workflows/raw/steps")"
status="ok"
note=""

if ! run_all_steps; then
  status="error"
  note="step execution failed"
fi

if [[ "$status" == "ok" ]]; then
  note="source_key=${RAW_SYNC_SOURCE_KEY}, host=${RAW_SYNC_HOST}, dry_run=${RAW_SYNC_DRY_RUN}, run_dir=${RUN_DIR_PATH}"
  db_set_state "last_raw_sync_status" "ok"
  db_set_state "last_raw_sync_note" "$note"
  db_set_state "last_raw_sync_at" "$(date +'%F %T')"
  db_job_finish "$job_id" "ok" "$note"
  log "raw sync ok run_dir=$RUN_DIR_PATH"
  [[ "$OK_FILE" == "/dev/null" ]] || touch "$OK_FILE"
else
  db_set_state "last_raw_sync_status" "error"
  db_set_state "last_raw_sync_note" "$note"
  db_job_finish "$job_id" "error" "$note"
  log "raw sync failed: $note"
  exit 20
fi