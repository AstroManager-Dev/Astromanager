#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local plan_json="${RUN_DIR_PATH}/sync_plan.json"
  local result_json="${RUN_DIR_PATH}/fetch_result.json"
  local dry_args=()

  [[ -f "$plan_json" ]] || die "sync plan missing: $plan_json"

  if [[ "${RAW_SYNC_DRY_RUN:-0}" == "1" ]]; then
    dry_args+=(--dry-run)
  fi

  PYTHONPATH="$ROOT/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 -m astromanager.raw.fetch_sync \
    --db-path "$DB_PATH" \
    --instance-key "$RAW_SYNC_INSTANCE_KEY" \
    --source-key "$RAW_SYNC_SOURCE_KEY" \
    --plan-json "$plan_json" \
    --result-json "$result_json" \
    "${dry_args[@]}"

  [[ -f "$result_json" ]] || die "fetch result missing: $result_json"
  log "fetch result saved: $result_json"
}
