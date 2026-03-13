#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

PLAN_JSON="${RUN_DIR_PATH}/sync_plan.json"
FETCH_JSON="${RUN_DIR_PATH}/fetch_result.json"

[[ -f "$PLAN_JSON" ]] || die "missing sync plan: $PLAN_JSON"

planned_total="$(python3 - <<'PY2' "$PLAN_JSON"
import json, sys
data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
print(int(data.get("plan_count", 0)))
PY2
)"

downloaded=0
skipped=0
errors=0
processed=0

raw_progress_log "$planned_total" "$processed" "$downloaded" "$skipped" "$errors" "0040_transfer_files.sh"

if [[ "${RAW_SYNC_DRY_RUN:-0}" == "1" ]]; then
  python3 - <<'PY2' "$PLAN_JSON" "$FETCH_JSON"
import json, sys
plan = json.load(open(sys.argv[1], "r", encoding="utf-8"))
items = plan.get("items", [])
skipped = 0
errors = 0
downloaded = 0
for item in items:
    action = item.get("action", "")
    if action == "download_new":
        pass
    else:
        skipped += 1
out = {
    "downloaded": downloaded,
    "skipped": skipped,
    "errors": errors,
}
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
PY2
  log "fetch result saved: $FETCH_JSON"
  exit 0
fi

python3 - <<'PY2' "$PLAN_JSON" | while IFS=$'\t' read -r action remote_path local_abs_path; do
import json, sys
plan = json.load(open(sys.argv[1], "r", encoding="utf-8"))
for item in plan.get("items", []):
    print(
        f"{item.get('action','')}\t{item.get('remote_path','')}\t{item.get('local_abs_path','')}"
    )
PY2
  [[ -n "$remote_path" && -n "$local_abs_path" ]] || continue

  case "$action" in
    skip_same)
      skipped=$((skipped + 1))
      ;;
    download_new|replace_changed)
      mkdir -p "$(dirname "$local_abs_path")"
      if python3 - <<'PY3' "$remote_path" "$local_abs_path"
import sys
from astromanager.raw.fetch_sync import fetch_one_file
remote_path = sys.argv[1]
local_abs_path = sys.argv[2]
fetch_one_file(
    host=sys.argv[3] if len(sys.argv) > 3 else "",
    user=sys.argv[4] if len(sys.argv) > 4 else "",
    password=sys.argv[5] if len(sys.argv) > 5 else "",
    remote_path=remote_path,
    local_abs_path=local_abs_path,
    timeout_seconds=int(sys.argv[6]) if len(sys.argv) > 6 else 60,
)
PY3 "$RAW_SYNC_HOST" "$RAW_SYNC_USER" "$RAW_SYNC_PASS" "$RAW_SYNC_TIMEOUT"; then
        downloaded=$((downloaded + 1))
      else
        errors=$((errors + 1))
      fi
      ;;
    *)
      skipped=$((skipped + 1))
      ;;
  esac

  processed=$((downloaded + skipped + errors))
  raw_progress_log "$planned_total" "$processed" "$downloaded" "$skipped" "$errors" "0040_transfer_files.sh"
done

python3 - <<'PY2' "$FETCH_JSON" "$downloaded" "$skipped" "$errors"
import json, sys
out = {
    "downloaded": int(sys.argv[2]),
    "skipped": int(sys.argv[3]),
    "errors": int(sys.argv[4]),
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
PY2

log "fetch result saved: $FETCH_JSON"
