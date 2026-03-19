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
SOURCE_KEY_FILTER="${SOURCE_KEY:-}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-dir) STATE_DIR_ARG="$2"; shift 2 ;;
    --log-dir) LOG_DIR_ARG="$2"; shift 2 ;;
    --source-key) SOURCE_KEY_FILTER="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "raw sync: unknown arg: $1" >&2; exit 2 ;;
  esac
done

ROOT="${ROOT:-/app}"
RAW_SYNC_DRY_RUN="$DRY_RUN"
RUN_ID="$(date +'%F_%H-%M-%S')"
BASE_RUN_DIR="${STATE_DIR_ARG%/}/run/raw_sync/${RUN_ID}"
STEPS_DIR="$ROOT/workflows/raw/steps"
LOCK_FILE="${LOCK_DIR%/}/raw_sync.lock"
INSTANCE_LIST_FILE="$BASE_RUN_DIR/instances.tsv"

mkdir -p "$BASE_RUN_DIR" "$LOG_DIR_ARG/steps" "$(dirname "$LOCK_FILE")"

LOG="$(mklog "${LOG_DIR_ARG%/}/steps" "raw_sync")"

if ! acquire_lock "$LOCK_FILE" 8; then
  echo "raw sync: lock busy: $LOCK_FILE" >&2
  exit 10
fi

export ROOT LOG DB_PATH RAW_ROOT RUNTIME_ROOT LOG_ROOT
export STATE_DIR_ARG LOG_DIR_ARG RAW_SYNC_DRY_RUN SOURCE_KEY_FILTER
export RUN_ID BASE_RUN_DIR STEPS_DIR

log "raw sync start source_filter=${SOURCE_KEY_FILTER:-all_active} dry_run=$RAW_SYNC_DRY_RUN"
log "ROOT=$ROOT"
log "DB_PATH=$DB_PATH"
log "RAW_ROOT=$RAW_ROOT"
log "STATE_DIR_ARG=$STATE_DIR_ARG"
log "LOG_DIR_ARG=$LOG_DIR_ARG"
log "STEPS_DIR=$STEPS_DIR"

db_init "$ROOT"

[[ -d "$STEPS_DIR" ]] || die "missing steps dir: $STEPS_DIR"

PYTHONPATH="$ROOT/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY' > "$INSTANCE_LIST_FILE"
import os
from astromanager.raw.device_instance import list_active_device_instances

db_path = os.environ["DB_PATH"]
source_key = os.environ.get("SOURCE_KEY_FILTER", "")
for instance in list_active_device_instances(db_path, source_key):
    print(f"{instance.instance_key}\t{instance.source_key}\t{instance.host}")
PY

[[ -s "$INSTANCE_LIST_FILE" ]] || die "no active device instances found"

run_step_file() {
  local step_file="$1"
  log "run step=$(basename "$step_file") instance=$RAW_SYNC_INSTANCE_KEY"
  # shellcheck source=/dev/null
  source "$step_file"
  declare -F step_run >/dev/null || die "step file has no step_run(): $step_file"
  step_run
  unset -f step_run
}

run_all_steps_for_instance() {
  local found=0
  local step_file

  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    found=1
    run_step_file "$step_file"
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)

  [[ "$found" -eq 1 ]] || die "no step files found in $STEPS_DIR"
}

job_id="$(db_job_start "raw_sync" "workflow" "controller auto-runs sorted step files from workflows/raw/steps per active device instance")"
note=""
processed_instances=0

run_all_instances() {
  local instance_key source_key host
  while IFS=$'\t' read -r instance_key source_key host; do
    [[ -n "$instance_key" ]] || continue
    processed_instances=$((processed_instances + 1))
    export RAW_SYNC_INSTANCE_KEY="$instance_key"
    export RAW_SYNC_SOURCE_KEY="$source_key"
    export RUN_DIR_PATH="$BASE_RUN_DIR/$instance_key"
    mkdir -p "$RUN_DIR_PATH"
    log "raw sync instance start instance=$RAW_SYNC_INSTANCE_KEY source=$RAW_SYNC_SOURCE_KEY host=$host dry_run=$RAW_SYNC_DRY_RUN"
    run_all_steps_for_instance
    log "raw sync instance ok instance=$RAW_SYNC_INSTANCE_KEY run_dir=$RUN_DIR_PATH"
  done < "$INSTANCE_LIST_FILE"
}

if run_all_instances; then
  note="instances=${processed_instances}, source_filter=${SOURCE_KEY_FILTER:-all_active}, run_dir=${BASE_RUN_DIR}, dry_run=${RAW_SYNC_DRY_RUN}"
  db_set_state "last_raw_sync_status" "ok"
  db_set_state "last_raw_sync_note" "$note"
  db_set_state "last_raw_sync_at" "$(date +'%F %T')"
  db_job_finish "$job_id" "ok" "$note"
  log "raw sync ok run_dir=$BASE_RUN_DIR"
else
  note="raw sync failed source_filter=${SOURCE_KEY_FILTER:-all_active}, run_dir=${BASE_RUN_DIR}, dry_run=${RAW_SYNC_DRY_RUN}"
  db_set_state "last_raw_sync_status" "error"
  db_set_state "last_raw_sync_note" "$note"
  db_set_state "last_raw_sync_at" "$(date +'%F %T')"
  db_job_finish "$job_id" "error" "$note"
  log "raw sync failed run_dir=$BASE_RUN_DIR"
  exit 20
fi
