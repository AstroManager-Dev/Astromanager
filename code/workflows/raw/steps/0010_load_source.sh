#!/usr/bin/env bash
# AstroManager
# Author: M. Pastor Nause
set -euo pipefail

# shellcheck source=/dev/null
source "$ROOT/lib/common.sh"

PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY' > "$RUN_DIR_PATH/source.env"
import os
from astromanager.raw.device_source import load_device_source
source = load_device_source(os.environ["DB_PATH"], os.environ["RAW_SYNC_SOURCE_KEY"])
print(f"RAW_SYNC_SOURCE_ID={source.id}")
print(f"RAW_SYNC_SOURCE_VENDOR={source.vendor}")
print(f"RAW_SYNC_SOURCE_MODEL={source.model}")
print(f"RAW_SYNC_SOURCE_PROTOCOL={source.protocol}")
import shlex; print(f"RAW_SYNC_SOURCE_ROOT_PATTERN={shlex.quote(source.root_pattern)}")
PY
# shellcheck source=/dev/null
source "$RUN_DIR_PATH/source.env"
log "raw source loaded id=$RAW_SYNC_SOURCE_ID model=$RAW_SYNC_SOURCE_MODEL protocol=$RAW_SYNC_SOURCE_PROTOCOL"
