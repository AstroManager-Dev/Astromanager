#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 50: ned"
  /app/bin/resolve_target_ned.sh
}
