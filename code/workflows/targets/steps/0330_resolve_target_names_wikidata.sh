#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step33: resolve target names from wikidata"

  local py="/app/bin/resolve_target_names_wikidata.py"
  [[ -f "$py" ]] || die "missing helper: $py"

  python3 "$py"

  log "targets step33: done"
}
