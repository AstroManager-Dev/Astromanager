#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step75: sync target_nasa_resolve"
  python3 /app/bin/sync_target_resolver_tables.py "$DB_PATH" nasa
}
