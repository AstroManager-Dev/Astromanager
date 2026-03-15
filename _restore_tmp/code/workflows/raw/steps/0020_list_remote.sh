#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local inventory_json="${RUN_DIR_PATH}/remote_inventory.json"

  PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 -m astromanager.raw.remote_inventory \
    --db-path "$DB_PATH" \
    --source-key "$RAW_SYNC_SOURCE_KEY" \
    --host "$RAW_SYNC_HOST" \
    --user "$RAW_SYNC_USER" \
    --password "$RAW_SYNC_PASS" \
    --timeout "$RAW_SYNC_TIMEOUT" \
    --output-json "$inventory_json"

  [[ -f "$inventory_json" ]] || die "remote inventory was not created: $inventory_json"
  log "remote inventory saved: $inventory_json"
}
