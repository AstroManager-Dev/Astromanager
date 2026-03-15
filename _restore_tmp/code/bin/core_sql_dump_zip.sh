#!/usr/bin/env bash
set -euo pipefail

SQL_DUMP_ROOT="${SQL_DUMP_ROOT:-/runtime/backups/sql}"
DB_PATH="${DB_PATH:-/runtime/pipeline.db}"
HOST_UID="${HOST_UID:-1000}"
HOST_GID="${HOST_GID:-1000}"

STAMP="$(date +%F_%H-%M-%S)"
OUT_DIR="${SQL_DUMP_ROOT}"
TMP_SQL="/tmp/pipeline_${STAMP}.sql"
OUT_ZIP="${OUT_DIR}/pipeline_${STAMP}.sql.zip"

mkdir -p "${OUT_DIR}"
sqlite3 "${DB_PATH}" .dump > "${TMP_SQL}"
python3 - <<'PY2' "${TMP_SQL}" "${OUT_ZIP}"
import sys, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(src, arcname=src.split('/')[-1])
PY2
rm -f "${TMP_SQL}"
chown "${HOST_UID}:${HOST_GID}" "${OUT_ZIP}" 2>/dev/null || true
echo "SQL dump zip created: ${OUT_ZIP}"
