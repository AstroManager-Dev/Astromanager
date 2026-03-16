#!/usr/bin/env bash
set -euo pipefail

PROJECT_CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
CORE_BACKUP_ROOT="${CORE_BACKUP_ROOT:-/project-core/_dev_backups/core}"
DB_PATH="${DB_PATH:-/runtime/pipeline.db}"
LOCAL_SQL_DUMP_DIR="${LOCAL_SQL_DUMP_DIR:-${PROJECT_CORE_ROOT}/local/backup_sql}"
LOCAL_SQL_DUMP_FILE="${LOCAL_SQL_DUMP_FILE:-${LOCAL_SQL_DUMP_DIR}/pipeline_latest.sql}"

HOST_UID="${HOST_UID:-1000}"
HOST_GID="${HOST_GID:-1000}"

normalize_core_ownership() {
  chown -R "${HOST_UID}:${HOST_GID}" "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
  chown "${HOST_UID}:${HOST_GID}" \
    "${PROJECT_CORE_ROOT}/VERSION" \
    "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" \
    "${PROJECT_CORE_ROOT}/CHANGELOG.md" \
    "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true
  if [ -d "${PROJECT_CORE_ROOT}/local" ]; then
    chown -R "${HOST_UID}:${HOST_GID}" "${PROJECT_CORE_ROOT}/local" 2>/dev/null || true
  fi
}

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -e "${src}" ]; then
    mkdir -p "$(dirname "${dst}")"
    cp -a "${src}" "${dst}"
  fi
}

STAMP="$(date +%F_%H-%M-%S)"
OUT_DIR="${CORE_BACKUP_ROOT}"
OUT_ZIP="${OUT_DIR}/core_backup_${STAMP}.zip"
STAGE_DIR="/tmp/core_backup_${STAMP}"
MANIFEST_PATH="${STAGE_DIR}/manifest.json"

mkdir -p "${OUT_DIR}" "${LOCAL_SQL_DUMP_DIR}"
chown -R "${HOST_UID}:${HOST_GID}" "${PROJECT_CORE_ROOT}/code" "${PROJECT_CORE_ROOT}/scripts" 2>/dev/null || true
chown "${HOST_UID}:${HOST_GID}" \
  "${PROJECT_CORE_ROOT}/VERSION" \
  "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" \
  "${PROJECT_CORE_ROOT}/CHANGELOG.md" \
  "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" 2>/dev/null || true

rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/core"

if [ ! -f "${DB_PATH}" ]; then
  echo "FEHLER: DB nicht gefunden: ${DB_PATH}" >&2
  exit 1
fi

rm -f "${LOCAL_SQL_DUMP_FILE}"
sqlite3 "${DB_PATH}" .dump > "${LOCAL_SQL_DUMP_FILE}"

if [ ! -s "${LOCAL_SQL_DUMP_FILE}" ]; then
  echo "FEHLER: SQL-Dump leer oder nicht erstellt: ${LOCAL_SQL_DUMP_FILE}" >&2
  exit 1
fi

copy_if_exists "${PROJECT_CORE_ROOT}/code" "${STAGE_DIR}/core/code"
copy_if_exists "${PROJECT_CORE_ROOT}/scripts" "${STAGE_DIR}/core/scripts"
copy_if_exists "${PROJECT_CORE_ROOT}/VERSION" "${STAGE_DIR}/core/VERSION"
copy_if_exists "${PROJECT_CORE_ROOT}/SCHEMA_VERSION" "${STAGE_DIR}/core/SCHEMA_VERSION"
copy_if_exists "${PROJECT_CORE_ROOT}/CHANGELOG.md" "${STAGE_DIR}/core/CHANGELOG.md"
copy_if_exists "${PROJECT_CORE_ROOT}/CHANGELOG.unreleased.md" "${STAGE_DIR}/core/CHANGELOG.unreleased.md"
copy_if_exists "${LOCAL_SQL_DUMP_FILE}" "${STAGE_DIR}/core/local/backup_sql/$(basename "${LOCAL_SQL_DUMP_FILE}")"

if [ ! -s "${STAGE_DIR}/core/local/backup_sql/$(basename "${LOCAL_SQL_DUMP_FILE}")" ]; then
  echo "FEHLER: SQL-Dump wurde nicht in das Backup-Staging kopiert." >&2
  exit 1
fi

python3 - <<'PY' "${MANIFEST_PATH}" "${PROJECT_CORE_ROOT}"
import datetime
import json
import sys

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
        "local/backup_sql/pipeline_latest.sql",
    ],
}
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2, ensure_ascii=False)
PY

python3 - <<'PY' "${STAGE_DIR}/core" "${OUT_ZIP}"
import os
import sys
import zipfile

src_root = sys.argv[1]
out_zip = sys.argv[2]

with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src_root):
        dirs.sort()
        files.sort()
        for name in files:
            full_path = os.path.join(root, name)
            arcname = os.path.relpath(full_path, src_root)
            zf.write(full_path, arcname)
PY

python3 - <<'PY' "${OUT_ZIP}" "local/backup_sql/$(basename "${LOCAL_SQL_DUMP_FILE}")"
import sys
import zipfile

zip_path = sys.argv[1]
required_member = sys.argv[2]

with zipfile.ZipFile(zip_path, "r") as zf:
    names = set(zf.namelist())
    if required_member not in names:
        raise SystemExit(f"FEHLER: SQL-Dump fehlt im Backup-ZIP: {required_member}")
    info = zf.getinfo(required_member)
    if info.file_size <= 0:
        raise SystemExit(f"FEHLER: SQL-Dump im Backup-ZIP ist leer: {required_member}")
PY

normalize_core_ownership

rm -rf "${STAGE_DIR}"
echo "CORE backup created: ${OUT_ZIP}"
echo "Included SQL dump: local/backup_sql/$(basename "${LOCAL_SQL_DUMP_FILE}")"
echo "Ownership normalized to ${HOST_UID}:${HOST_GID}"
