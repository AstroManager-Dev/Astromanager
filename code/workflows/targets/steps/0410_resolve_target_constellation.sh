#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0410: resolve constellation from preferred coordinates"
  python3 /app/bin/resolve_target_constellation.py
}
