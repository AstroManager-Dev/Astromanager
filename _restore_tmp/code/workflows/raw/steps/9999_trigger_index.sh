#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

RESULT_JSON="${RUN_DIR_PATH}/fetch_result.json"

if [[ "${RAW_SYNC_DRY_RUN:-0}" == "1" ]]; then
  log "raw trigger index: skip dry-run"
  exit 0
fi

if [[ ! -f "$RESULT_JSON" ]]; then
  log "raw trigger index: skip missing fetch_result.json"
  exit 0
fi

DOWNLOADED_COUNT="$(python3 - <<'PY' "$RESULT_JSON"
import json, sys
p = sys.argv[1]
with open(p, "r", encoding="utf-8") as fh:
    data = json.load(fh)
print(int(data.get("counters", {}).get("downloaded", 0)))
PY
)"

if [[ "$DOWNLOADED_COUNT" -le 0 ]]; then
  log "raw trigger index: skip downloaded=0"
  exit 0
fi

log "raw trigger index: start astroctl index sessions downloaded=$DOWNLOADED_COUNT"
"$ROOT/bin/astroctl" index sessions >>"$LOG" 2>&1
log "raw trigger index: done astroctl index sessions"
