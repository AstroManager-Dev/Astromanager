#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0370: ned"
  python3 /app/bin/resolve_target_ned.py
}
