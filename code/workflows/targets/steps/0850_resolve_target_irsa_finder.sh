#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step95: irsa finder"
  python3 /app/bin/resolve_target_irsa_finder.py
}
