#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local inventory_json="${RUN_DIR_PATH}/remote_inventory.json"
  local plan_json="${RUN_DIR_PATH}/sync_plan.json"

  [[ -f "$inventory_json" ]] || die "missing remote inventory: $inventory_json"

  PYTHONPATH="$ROOT/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 -m astromanager.raw.plan_sync \
    --db-path "$DB_PATH" \
    --source-key "$RAW_SYNC_SOURCE_KEY" \
    --inventory-json "$inventory_json" \
    --raw-root "$RAW_ROOT" \
    --output-json "$plan_json"

  [[ -f "$plan_json" ]] || die "sync plan was not created: $plan_json"
  log "sync plan saved: $plan_json"
}
