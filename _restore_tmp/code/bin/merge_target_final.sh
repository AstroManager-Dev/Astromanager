#!/usr/bin/env bash
set -euo pipefail
exec python3 /app/bin/merge_target_final.py "$@"
