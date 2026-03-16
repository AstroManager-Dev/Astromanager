#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "index step45: sync session_platesolve_resolve"
  python3 /app/bin/sync_session_resolver_tables.py "$DB_PATH" platesolve
}
