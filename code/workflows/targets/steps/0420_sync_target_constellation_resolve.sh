#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step65: sync target_constellation_resolve"
  python3 /app/bin/sync_target_resolver_tables.py "$DB_PATH" constellation
}
