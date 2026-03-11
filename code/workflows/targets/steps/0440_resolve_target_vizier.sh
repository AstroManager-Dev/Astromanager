#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0440: resolve target vizier via tap"
  python3 /app/bin/resolve_target_vizier.py
}
