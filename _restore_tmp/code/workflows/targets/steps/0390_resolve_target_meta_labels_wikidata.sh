#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step 0390: resolve target meta labels from wikidata"
  python3 /app/bin/resolve_target_meta_labels_wikidata.py
}
