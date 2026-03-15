#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step85: skyview preview"
  python3 /app/bin/resolve_target_skyview.py
}
