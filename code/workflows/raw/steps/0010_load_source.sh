#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local source_env="${RUN_DIR_PATH}/source.env"

  PYTHONPATH="/app/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY' > "$source_env"
import os
import shlex
from astromanager.raw.device_source import load_device_source

source = load_device_source(os.environ["DB_PATH"], os.environ["RAW_SYNC_SOURCE_KEY"])

print(f"RAW_SYNC_SOURCE_ID={source.id}")
print(f"RAW_SYNC_SOURCE_VENDOR={shlex.quote(source.vendor)}")
print(f"RAW_SYNC_SOURCE_MODEL={shlex.quote(source.model)}")
print(f"RAW_SYNC_SOURCE_PROTOCOL={shlex.quote(source.protocol)}")
print(f"RAW_SYNC_SOURCE_ROOT_PATTERN={shlex.quote(source.root_pattern)}")
PY

  [[ -f "$source_env" ]] || die "source env was not created: $source_env"

  # shellcheck source=/dev/null
  source "$source_env"

  export RAW_SYNC_SOURCE_ID
  export RAW_SYNC_SOURCE_VENDOR
  export RAW_SYNC_SOURCE_MODEL
  export RAW_SYNC_SOURCE_PROTOCOL
  export RAW_SYNC_SOURCE_ROOT_PATTERN

  log "raw source loaded id=$RAW_SYNC_SOURCE_ID model=$RAW_SYNC_SOURCE_MODEL protocol=$RAW_SYNC_SOURCE_PROTOCOL"
}
