#!/usr/bin/env bash
set -euo pipefail

: "${RAW_ROOT:=/raw}"
: "${DATA_ROOT:=/data}"

: "${CATALOG_ROOT:=/data/catalog}"
: "${MASTERDARK_ROOT:=/data/masterdarks}"
: "${PREVIEW_ROOT:=/data/previews}"
: "${EXPORT_ROOT:=/data/export}"

: "${RUNTIME_ROOT:=/runtime}"
: "${LOCK_DIR:=/runtime/locks}"
: "${OK_DIR:=/runtime/ok}"
: "${QUEUE_DIR:=/runtime/queue}"
: "${RUN_DIR:=/runtime/run}"
: "${DB_PATH:=/runtime/pipeline.db}"

: "${LOG_ROOT:=/logs}"
: "${WORK_ROOT:=/work}"
: "${TMP_ROOT:=/tmp}"
: "${CACHE_ROOT:=/cache}"
: "${CONFIG_ROOT:=/config}"
