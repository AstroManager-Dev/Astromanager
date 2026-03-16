#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0350: simbad"
  python3 /app/bin/resolve_target_simbad.py
}
