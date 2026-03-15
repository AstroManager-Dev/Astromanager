#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 70: nasa image"
  /app/bin/resolve_target_nasa_image.sh
}
