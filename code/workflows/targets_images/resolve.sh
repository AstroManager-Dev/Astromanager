#!/usr/bin/env bash
set -euo pipefail
exec /app/workflows/targets/resolve.sh --workflow images "$@"
