#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

INVENTORY_JSON="$RUN_DIR_PATH/remote_inventory.json"
PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" \
python3 -m astromanager.raw.remote_inventory \
  --db-path "$DB_PATH" \
  --source-key "$RAW_SYNC_SOURCE_KEY" \
  --host "$RAW_SYNC_HOST" \
  --user "$RAW_SYNC_USER" \
  --password "$RAW_SYNC_PASS" \
  --timeout "$RAW_SYNC_TIMEOUT" \
  --output-json "$INVENTORY_JSON" >> "$LOG" 2>&1
log "remote inventory saved: $INVENTORY_JSON"
