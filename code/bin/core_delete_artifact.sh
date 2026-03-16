#!/usr/bin/env bash
set -euo pipefail

PROJECT_CORE_ROOT="${PROJECT_CORE_ROOT:-/project-core}"
CORE_BACKUP_ROOT="${CORE_BACKUP_ROOT:-/runtime/backups/core}"
SQL_DUMP_ROOT="${SQL_DUMP_ROOT:-/runtime/backups/sql}"
HOST_UID="${HOST_UID:-1000}"
HOST_GID="${HOST_GID:-1000}"

BUCKET="${1:-}"
NAME="${2:-}"

if [ -z "$BUCKET" ] || [ -z "$NAME" ]; then
  echo "Usage: core_delete_artifact.sh <backup|sql> <filename>"
  exit 1
fi

case "$BUCKET" in
  backup) ROOT="$CORE_BACKUP_ROOT" ;;
  sql) ROOT="$SQL_DUMP_ROOT" ;;
  *) echo "Ungültiger Bucket: $BUCKET"; exit 1 ;;
esac

SAFE_NAME="$(basename -- "$NAME")"
TARGET="${ROOT}/${SAFE_NAME}"

if [ ! -f "$TARGET" ]; then
  echo "Datei nicht gefunden: $TARGET"
  exit 1
fi

rm -f "$TARGET"
chown -R "${HOST_UID}:${HOST_GID}" "$ROOT" 2>/dev/null || true
echo "Deleted ${BUCKET}: ${SAFE_NAME}"
