#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step82: sync target_legacy_survey_resolve"
  python3 /app/bin/sync_target_resolver_tables.py /runtime/pipeline.db legacy
}
