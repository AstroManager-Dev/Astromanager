#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local plan_json="${RUN_DIR_PATH}/sync_plan.json"
  local fetch_json="${RUN_DIR_PATH}/fetch_result.json"
  local summary_json="${RUN_DIR_PATH}/summary.json"

  [[ -f "$plan_json" ]] || die "missing sync plan for finalize: $plan_json"
  [[ -f "$fetch_json" ]] || die "missing fetch result for finalize: $fetch_json"

  python3 - <<'PY' "$plan_json" "$fetch_json" "$summary_json"
import json
import sys
from pathlib import Path

plan_path = Path(sys.argv[1])
fetch_path = Path(sys.argv[2])
summary_path = Path(sys.argv[3])

plan = json.loads(plan_path.read_text(encoding="utf-8"))
fetch = json.loads(fetch_path.read_text(encoding="utf-8"))

plan_count = int(plan.get("plan_count", 0))
plan_counters = plan.get("counters", {}) or {}

if "counters" in fetch and isinstance(fetch["counters"], dict):
    result_counters = fetch["counters"]
else:
    result_counters = {
        "downloaded": int(fetch.get("downloaded", 0)),
        "skipped": int(fetch.get("skipped", 0)),
        "errors": int(fetch.get("errors", 0)),
    }

summary = {
    "source_key": plan.get("source_key", ""),
    "plan_count": plan_count,
    "plan_counters": plan_counters,
    "result_counters": {
        "downloaded": int(result_counters.get("downloaded", 0)),
        "skipped": int(result_counters.get("skipped", 0)),
        "errors": int(result_counters.get("errors", 0)),
    },
}

summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
PY

  [[ -f "$summary_json" ]] || die "summary was not created: $summary_json"
  log "raw sync summary: $(cat "$summary_json")"
}
