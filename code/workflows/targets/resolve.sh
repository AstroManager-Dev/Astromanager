#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
source "$ROOT/lib/pipeline_env.sh"
source "$ROOT/lib/common.sh"
source "$ROOT/lib/db.sh"

LOG_DIR_ARG="${LOG_DIR:-$LOG_ROOT}"
DRY_RUN=0
WORKFLOW="all"
STEPS_DIR="$ROOT/workflows/targets/steps"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --log-dir) LOG_DIR_ARG="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --workflow) WORKFLOW="$2"; shift 2 ;;
    *) echo "targets resolve: unknown arg: $1" >&2; exit 2 ;;
  esac
done

LOG="$(mklog "${LOG_DIR_ARG%/}/steps" "targets_resolve")"
LOCK_FILE="${LOCK_DIR%/}/targets_resolve.lock"

mkdir -p "$LOG_DIR_ARG" "$(dirname "$LOCK_FILE")"

if ! acquire_lock "$LOCK_FILE" 8; then
  echo "targets resolve: lock busy: $LOCK_FILE" >&2
  exit 10
fi

log "targets resolve: start"
log "DB_PATH=$DB_PATH"
log "DRY_RUN=$DRY_RUN"
log "WORKFLOW=$WORKFLOW"
log "STEPS_DIR=$STEPS_DIR"

db_init "$ROOT"
[[ -d "$STEPS_DIR" ]] || die "missing steps dir: $STEPS_DIR"

step_num_of() {
  local base="$1"
  local raw="${base%%_*}"
  echo $((10#$raw))
}

want_step() {
  local base="$1"
  local step_num
  step_num="$(step_num_of "$base")"

  case "$WORKFLOW" in
    data)
      [[ "$step_num" -ge 1 && "$step_num" -le 299 ]]
      ;;
    info)
      [[ "$step_num" -ge 300 && "$step_num" -le 799 ]]
      ;;
    images)
      [[ "$step_num" -ge 800 && "$step_num" -le 1299 ]]
      ;;
    all)
      return 0
      ;;
    *)
      die "unknown workflow: $WORKFLOW"
      ;;
  esac
}

run_step_file() {
  local step_file="$1"
  log "run step: $(basename "$step_file")"
  source "$step_file"
  declare -F step_run >/dev/null || die "step file has no step_run(): $step_file"
  step_run
  unset -f step_run
}

run_all_steps() {
  local found=0
  local step_file
  local base

  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    base="$(basename "$step_file")"
    if ! want_step "$base"; then
      continue
    fi
    found=1
    run_step_file "$step_file"
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)

  [[ "$found" -eq 1 ]] || die "no matching step files found in $STEPS_DIR for workflow=$WORKFLOW"
}

run_id="$(db_job_start "targets_resolve_${WORKFLOW}" "workflow" "controller runs target resolver steps")"
status="ok"
note=""

if [[ "$DRY_RUN" -eq 1 ]]; then
  while IFS= read -r step_file; do
    [[ -n "$step_file" ]] || continue
    base="$(basename "$step_file")"
    if want_step "$base"; then
      log "dry-run step: $base"
    fi
  done < <(find "$STEPS_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sh' | sort)
else
  if ! run_all_steps; then
    status="error"
    note="target resolver step execution failed"
  fi
fi

if [[ "$status" == "ok" ]]; then
  note="workflow=${WORKFLOW} dry_run=${DRY_RUN}"
  db_set_state "last_targets_resolve_status" "ok"
  db_set_state "last_targets_resolve_note" "$note"
  db_set_state "last_targets_resolve_at" "$(date +'%F %T')"
  db_job_finish "$run_id" "ok" "$note"
  log "targets resolve: success"
  log "$note"
else
  db_set_state "last_targets_resolve_status" "error"
  db_set_state "last_targets_resolve_note" "$note"
  db_job_finish "$run_id" "error" "$note"
  log "targets resolve: failed: $note"
  exit 20
fi
