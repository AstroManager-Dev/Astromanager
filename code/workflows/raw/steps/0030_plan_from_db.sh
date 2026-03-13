#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

INVENTORY_JSON="$RUN_DIR_PATH/remote_inventory.json"
PLAN_JSON="$RUN_DIR_PATH/sync_plan.json"
PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" \
python3 /app/bin/raw/sync_plan.py \
  --db-path "$DB_PATH" \
  --inventory-json "$INVENTORY_JSON" \
  --raw-root "$RAW_ROOT" \
  --source-key "$RAW_SYNC_SOURCE_KEY" \
  --output-json "$PLAN_JSON" >> "$LOG" 2>&1
log "sync plan saved: $PLAN_JSON"
