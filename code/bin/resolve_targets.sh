#!/usr/bin/env bash
set -euo pipefail

: "${DB_PATH:=/runtime/pipeline.db}"

python3 /app/bin/resolve_targets.py "$@"
