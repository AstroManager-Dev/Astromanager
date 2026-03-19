#!/usr/bin/env bash
set -euo pipefail

step_run() {
  local instance_env="${RUN_DIR_PATH}/instance.env"

  PYTHONPATH="$ROOT/lib/py${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY' > "$instance_env"
import os
import shlex
from astromanager.raw.device_instance import load_device_instance

instance = load_device_instance(os.environ["DB_PATH"], os.environ["RAW_SYNC_INSTANCE_KEY"])

print(f"RAW_SYNC_INSTANCE_ID={instance.id}")
print(f"RAW_SYNC_INSTANCE_KEY={shlex.quote(instance.instance_key)}")
print(f"RAW_SYNC_INSTANCE_NAME={shlex.quote(instance.display_name)}")
print(f"RAW_SYNC_SOURCE_ID={instance.source_id}")
print(f"RAW_SYNC_SOURCE_KEY={shlex.quote(instance.source_key)}")
print(f"RAW_SYNC_SOURCE_VENDOR={shlex.quote(instance.vendor)}")
print(f"RAW_SYNC_SOURCE_MODEL={shlex.quote(instance.model)}")
print(f"RAW_SYNC_SOURCE_PROTOCOL={shlex.quote(instance.protocol)}")
print(f"RAW_SYNC_SOURCE_ROOT_PATTERN={shlex.quote(instance.root_pattern)}")
print(f"RAW_SYNC_HOST={shlex.quote(instance.host)}")
print(f"RAW_SYNC_PORT={instance.port}")
print(f"RAW_SYNC_USER={shlex.quote(instance.username)}")
print(f"RAW_SYNC_PASS={shlex.quote(instance.password_text)}")
print(f"RAW_SYNC_TIMEOUT={instance.timeout_seconds}")
print(f"RAW_SYNC_REMOTE_BASE_DIR={shlex.quote(instance.remote_base_dir)}")
print(f"RAW_SYNC_ALLOWED_EXTENSIONS={shlex.quote(instance.allowed_extensions_csv)}")
PY

  [[ -f "$instance_env" ]] || die "instance env was not created: $instance_env"

  # shellcheck source=/dev/null
  source "$instance_env"

  export RAW_SYNC_INSTANCE_ID
  export RAW_SYNC_INSTANCE_KEY
  export RAW_SYNC_INSTANCE_NAME
  export RAW_SYNC_SOURCE_ID
  export RAW_SYNC_SOURCE_KEY
  export RAW_SYNC_SOURCE_VENDOR
  export RAW_SYNC_SOURCE_MODEL
  export RAW_SYNC_SOURCE_PROTOCOL
  export RAW_SYNC_SOURCE_ROOT_PATTERN
  export RAW_SYNC_HOST
  export RAW_SYNC_PORT
  export RAW_SYNC_USER
  export RAW_SYNC_PASS
  export RAW_SYNC_TIMEOUT
  export RAW_SYNC_REMOTE_BASE_DIR
  export RAW_SYNC_ALLOWED_EXTENSIONS

  log "raw source loaded instance=$RAW_SYNC_INSTANCE_KEY id=$RAW_SYNC_INSTANCE_ID model=$RAW_SYNC_SOURCE_MODEL protocol=$RAW_SYNC_SOURCE_PROTOCOL host=$RAW_SYNC_HOST"
}
