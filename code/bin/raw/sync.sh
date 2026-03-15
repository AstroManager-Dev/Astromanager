#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail
exec /app/workflows/raw/sync.sh "$@"
