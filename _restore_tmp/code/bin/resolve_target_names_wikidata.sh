#!/usr/bin/env bash
set -euo pipefail
exec python3 /app/bin/resolve_target_names_wikidata.py "$@"
