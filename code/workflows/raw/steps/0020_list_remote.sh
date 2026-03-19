#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local inventory_json="${RUN_DIR_PATH}/remote_inventory.json"

  PYTHONPATH="$ROOT/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 -m astromanager.raw.remote_inventory \
    --db-path "$DB_PATH" \
    --instance-key "$RAW_SYNC_INSTANCE_KEY" \
    --source-key "$RAW_SYNC_SOURCE_KEY" \
    --output-json "$inventory_json"

  [[ -f "$inventory_json" ]] || die "remote inventory was not created: $inventory_json"
  log "remote inventory saved: $inventory_json"
}
