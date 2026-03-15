#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step31: sesame info"
  python3 /app/bin/resolve_target_sesame.py
}
