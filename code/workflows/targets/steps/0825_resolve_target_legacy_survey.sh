#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step82: legacy survey"
  python3 /app/bin/resolve_target_legacy_survey.py
}
