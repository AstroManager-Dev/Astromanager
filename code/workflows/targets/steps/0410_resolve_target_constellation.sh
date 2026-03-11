#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 60: constellation"
  /app/bin/resolve_target_constellation.sh
}
