#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0400: sync target_wikidata_meta_resolve"
  python3 /app/bin/sync_target_resolver_tables.py "$DB_PATH" wikidata_meta
}
