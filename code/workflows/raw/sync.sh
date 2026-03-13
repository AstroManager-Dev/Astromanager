#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"

# shellcheck source=/dev/null
source "$ROOT/lib/pipeline_env.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/db.sh"

STATE_DIR_ARG="${STATE_DIR:-$RUNTIME_ROOT}"
LOG_DIR_ARG="${LOG_DIR:-$LOG_ROOT}"
SOURCE_KEY="${SOURCE_KEY:-dwarflab_dwarf3}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR_ARG="$2"; shift 2 ;;
    --log-dir) LOG_DIR_ARG="$2"; shift 2 ;;
    --source-key) SOURCE_KEY="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "raw sync: unknown arg: $1" >&2; exit 2 ;;
  esac
done

ROOT="${ROOT:-/app}"
RAW_SYNC_SOURCE_KEY="$SOURCE_KEY"
RAW_SYNC_DRY_RUN="$DRY_RUN"

RAW_SYNC_HOST="${RAW_SYNC_HOST:-${DWARF_HOST:-192.168.2.163}}"
RAW_SYNC_USER="${RAW_SYNC_USER:-${DWARF_USER:-anonymous}}"
RAW_SYNC_PASS="${RAW_SYNC_PASS:-${DWARF_PASS:-}}"
RAW_SYNC_TIMEOUT="${RAW_SYNC_TIMEOUT:-15}"

RUN_ID="$(date +'%F_%H-%M-%S')"
RUN_DIR_PATH="${STATE_DIR_ARG%/}/run/raw_sync/${RUN_ID}"
STEPS_DIR="$ROOT/workflows/raw/steps"
LOCK_FILE="${LOCK_DIR%/}/raw_sync.lock"

mkdir -p "$RUN_DIR_PATH" "$LOG_DIR_ARG/steps" "$(dirname "$LOCK_FILE")"

LOG="$(mklog "${LOG_DIR_ARG%/}/steps" "raw_sync")"

if ! acquire_lock "$LOCK_FILE" 8; then
  echo "raw sync: lock busy: $LOCK_FILE" >&2
  exit 10
fi

export ROOT LOG DB_PATH RAW_ROOT RUNTIME_ROOT LOG_ROOT
export STATE_DIR_ARG LOG_DIR_ARG
export RAW_SYNC_SOURCE_KEY RAW_SYNC_DRY_RUN
export RAW_SYNC_HOST RAW_SYNC_USER RAW_SYNC_PASS RAW_SYNC_TIMEOUT
export RUN_ID RUN_DIR_PATH STEPS_DIR

log "raw sync start source=$RAW_SYNC_SOURCE_KEY host=$RAW_SYNC_HOST dry_run=$RAW_SYNC_DRY_RUN"
log "ROOT=$ROOT"
log "DB_PATH=$DB_PATH"
log "RAW_ROOT=$RAW_ROOT"
log "STATE_DIR_ARG=$STATE_DIR_ARG"
log "LOG_DIR_ARG=$LOG_DIR_ARG"
log "STEPS_DIR=$STEPS_DIR"

db_init "$ROOT"

[[ -d "$STEPS_DIR" ]] || die "missing steps dir: $STEPS_DIR"

run_step_file() {
  local step_file="$1"
  log "run step=$(basename "$step_file")"
  # shellcheck source=/dev/null
  source "$step_file"
  declare -F step_run >/dev/null || die "step file has no step_run(): $step_file"
  step_run
  unset -f step_run
}

run_all_steps() {
  local found=0
  local step_file

  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    found=1
    run_step_file "$step_file"
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)

  [[ "$found" -eq 1 ]] || die "no step files found in $STEPS_DIR"
}

job_id="$(db_job_start "raw_sync" "workflow" "controller auto-runs sorted step files from workflows/raw/steps")"
note=""

if run_all_steps; then
  note="source_key=${RAW_SYNC_SOURCE_KEY}, host=${RAW_SYNC_HOST}, run_dir=${RUN_DIR_PATH}, dry_run=${RAW_SYNC_DRY_RUN}"
  db_set_state "last_raw_sync_status" "ok"
  db_set_state "last_raw_sync_note" "$note"
  db_set_state "last_raw_sync_at" "$(date +'%F %T')"
  db_job_finish "$job_id" "ok" "$note"
  log "raw sync ok run_dir=$RUN_DIR_PATH"
else
  note="raw sync failed source_key=${RAW_SYNC_SOURCE_KEY}, host=${RAW_SYNC_HOST}, run_dir=${RUN_DIR_PATH}, dry_run=${RAW_SYNC_DRY_RUN}"
  db_set_state "last_raw_sync_status" "error"
  db_set_state "last_raw_sync_note" "$note"
  db_set_state "last_raw_sync_at" "$(date +'%F %T')"
  db_job_finish "$job_id" "error" "$note"
  log "raw sync failed run_dir=$RUN_DIR_PATH"
  exit 20
fi
