#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step100: sync target_irsa_resolve"
  python3 /app/bin/sync_target_resolver_tables.py /runtime/pipeline.db irsa
}
