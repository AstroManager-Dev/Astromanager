#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "index step65: sync session_target_resolve"
  python3 /app/bin/sync_session_resolver_tables.py "$DB_PATH" targetresolve
}
