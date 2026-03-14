#!/usr/bin/env bash
set -euo pipefail

CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
BACKUP_ROOT="${CORE_BACKUP_ROOT:-/runtime/backups/core}"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
LABEL="${1:-webui}"
OUT_DIR="${BACKUP_ROOT}"
OUT_ZIP="${OUT_DIR}/astromanager_core_${STAMP}_${LABEL}.zip"
STAGE_DIR="$(mktemp -d /tmp/am_core_backup.XXXXXX)"

cleanup() {
  rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

if [[ ! -d "$CORE_ROOT" ]]; then
  echo "ERROR: PROJECT_CORE_ROOT not found: $CORE_ROOT" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
mkdir -p "$STAGE_DIR/core"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  fi
}

copy_if_exists "$CORE_ROOT/code" "$STAGE_DIR/core/code"
copy_if_exists "$CORE_ROOT/scripts" "$STAGE_DIR/core/scripts"
copy_if_exists "$CORE_ROOT/VERSION" "$STAGE_DIR/core/VERSION"
copy_if_exists "$CORE_ROOT/SCHEMA_VERSION" "$STAGE_DIR/core/SCHEMA_VERSION"
copy_if_exists "$CORE_ROOT/CHANGELOG.md" "$STAGE_DIR/core/CHANGELOG.md"
copy_if_exists "$CORE_ROOT/CHANGELOG.unreleased.md" "$STAGE_DIR/core/CHANGELOG.unreleased.md"

python3 - <<'PY2' "$STAGE_DIR/core/manifest.json" "$CORE_ROOT"
import json, sys, datetime
manifest_path = sys.argv[1]
core_root = sys.argv[2]
manifest = {
    "backup_type": "core",
    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "core_root": core_root,
    "items": [
        "code/",
        "scripts/",
        "VERSION",
        "SCHEMA_VERSION",
        "CHANGELOG.md",
        "CHANGELOG.unreleased.md",
    ],
}
with open(manifest_path, 'w', encoding='utf-8') as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
PY2

(
  cd "$STAGE_DIR/core"
  zip -qr "$OUT_ZIP" .
)

echo "CORE backup created: $OUT_ZIP"
