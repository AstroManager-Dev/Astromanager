#!/usr/bin/env bash
set -euo pipefail

ZIP_PATH="${1:-}"
CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"

if [[ -z "$ZIP_PATH" ]]; then
  echo "Usage: core_restore_zip.sh /path/to/backup.zip" >&2
  exit 1
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "ERROR: ZIP not found: $ZIP_PATH" >&2
  exit 1
fi

if [[ ! -d "$CORE_ROOT" ]]; then
  echo "ERROR: PROJECT_CORE_ROOT not found: $CORE_ROOT" >&2
  exit 1
fi

python3 - <<'PY' "$ZIP_PATH" "$CORE_ROOT"
from pathlib import Path
import shutil, sys, zipfile
zip_path = Path(sys.argv[1])
core_root = Path(sys.argv[2])
allowed_top = {"code", "scripts", "VERSION", "SCHEMA_VERSION", "CHANGELOG.md", "CHANGELOG.unreleased.md", "manifest.json"}
stage = Path('/tmp/am_core_restore_stage')
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(zip_path) as zf:
    names = [n for n in zf.namelist() if n and not n.endswith('/')]
    bad = []
    for name in names:
        top = Path(name).parts[0]
        if top not in allowed_top:
            bad.append(name)
    if bad:
        raise SystemExit(f"ERROR: ZIP contains disallowed paths: {bad[:10]}")
    zf.extractall(stage)
for item in ["code", "scripts", "VERSION", "SCHEMA_VERSION", "CHANGELOG.md", "CHANGELOG.unreleased.md"]:
    src = stage / item
    dst = core_root / item
    if not src.exists():
        continue
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
print(f"CORE restore completed from {zip_path} to {core_root}")
PY
