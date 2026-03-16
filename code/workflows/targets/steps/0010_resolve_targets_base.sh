#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 10: sesame base resolve"
  /app/bin/resolve_targets.sh
}
