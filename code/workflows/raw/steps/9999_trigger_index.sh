#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

step_run() {
  local result_json="${RUN_DIR_PATH}/fetch_result.json"
  local downloaded_count

  if [[ "${RAW_SYNC_DRY_RUN:-0}" == "1" ]]; then
    log "raw trigger index: skip dry-run instance=$RAW_SYNC_INSTANCE_KEY"
    return 0
  fi

  if [[ ! -f "$result_json" ]]; then
    log "raw trigger index: skip missing fetch_result.json instance=$RAW_SYNC_INSTANCE_KEY"
    return 0
  fi

  downloaded_count="$(python3 - <<'PY' "$result_json"
import json, sys
p = sys.argv[1]
with open(p, "r", encoding="utf-8") as fh:
    data = json.load(fh)
print(int(data.get("counters", {}).get("downloaded", 0)))
PY
)"

  if [[ "$downloaded_count" -le 0 ]]; then
    log "raw trigger index: skip downloaded=0 instance=$RAW_SYNC_INSTANCE_KEY"
    return 0
  fi

  log "raw trigger index: start astroctl index sessions instance=$RAW_SYNC_INSTANCE_KEY downloaded=$downloaded_count"
  "$ROOT/bin/astroctl" index sessions >>"$LOG" 2>&1
  log "raw trigger index: done astroctl index sessions instance=$RAW_SYNC_INSTANCE_KEY"
}
