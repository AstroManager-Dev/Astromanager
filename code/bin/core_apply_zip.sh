#!/usr/bin/env bash
set -euo pipefail
ZIP_PATH="${1:-}"
/app/bin/core_restore_zip.sh "$ZIP_PATH"
