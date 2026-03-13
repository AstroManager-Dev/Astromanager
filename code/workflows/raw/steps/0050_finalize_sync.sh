#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

PLAN_JSON="$RUN_DIR_PATH/sync_plan.json"
RESULT_JSON="$RUN_DIR_PATH/fetch_result.json"
SUMMARY_JSON="$RUN_DIR_PATH/summary.json"
export PLAN_JSON RESULT_JSON RAW_SYNC_SOURCE_KEY
python3 - <<'PY' > "$SUMMARY_JSON"
import json, os
with open(os.environ['PLAN_JSON'], 'r', encoding='utf-8') as fh:
    plan = json.load(fh)
with open(os.environ['RESULT_JSON'], 'r', encoding='utf-8') as fh:
    result = json.load(fh)
summary = {
    'source_key': os.environ['RAW_SYNC_SOURCE_KEY'],
    'plan_count': plan.get('plan_count', 0),
    'plan_counters': plan.get('counters', {}),
    'result_counters': result.get('counters', {}),
}
print(json.dumps(summary, ensure_ascii=False, separators=(',', ':')))
PY
log "raw sync summary: $(cat "$SUMMARY_JSON")"
