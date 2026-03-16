#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0460: merge target_final"
  python3 /app/bin/merge_target_final.py
}
