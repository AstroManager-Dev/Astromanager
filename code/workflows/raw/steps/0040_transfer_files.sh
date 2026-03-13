#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

PLAN_JSON="$RUN_DIR_PATH/sync_plan.json"
RESULT_JSON="$RUN_DIR_PATH/fetch_result.json"
EXTRA_ARGS=()
[[ "$RAW_SYNC_DRY_RUN" == "1" ]] && EXTRA_ARGS+=(--dry-run)
PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" \
python3 /app/bin/raw/sync_fetch.py \
  --db-path "$DB_PATH" \
  --source-key "$RAW_SYNC_SOURCE_KEY" \
  --host "$RAW_SYNC_HOST" \
  --user "$RAW_SYNC_USER" \
  --password "$RAW_SYNC_PASS" \
  --timeout "$RAW_SYNC_TIMEOUT" \
  --plan-json "$PLAN_JSON" \
  --result-json "$RESULT_JSON" \
  "${EXTRA_ARGS[@]}" >> "$LOG" 2>&1
log "fetch result saved: $RESULT_JSON"
