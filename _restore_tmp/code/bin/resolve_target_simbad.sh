#!/usr/bin/env bash
set -euo pipefail
exec python3 /app/bin/resolve_target_simbad.py "$@"
