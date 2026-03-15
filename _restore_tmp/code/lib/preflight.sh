#!/usr/bin/env bash
set -euo pipefail

preflight() {
  local required_dirs=(
    "${RAW_ROOT:-}"
    "${DATA_ROOT:-}"
    "${CATALOG_ROOT:-}"
    "${MASTERDARK_ROOT:-}"
    "${PREVIEW_ROOT:-}"
    "${EXPORT_ROOT:-}"
    "${RUNTIME_ROOT:-}"
    "${LOCK_DIR:-}"
    "${OK_DIR:-}"
    "${QUEUE_DIR:-}"
    "${RUN_DIR:-}"
    "${LOG_ROOT:-}"
    "${WORK_ROOT:-}"
    "${TMP_ROOT:-}"
    "${CACHE_ROOT:-}"
    "${CONFIG_ROOT:-}"
    "${STEPS_DIR:-}"
  )

  local d
  for d in "${required_dirs[@]}"; do
    if [[ -z "$d" ]]; then
      echo "preflight: empty required directory variable" >&2
      exit 2
    fi
  done

  mkdir -p \
    "$DATA_ROOT" \
    "$CATALOG_ROOT" \
    "$MASTERDARK_ROOT" \
    "$PREVIEW_ROOT" \
    "$EXPORT_ROOT" \
    "$RUNTIME_ROOT" \
    "$LOCK_DIR" \
    "$OK_DIR" \
    "$QUEUE_DIR" \
    "$RUN_DIR" \
    "$LOG_ROOT" \
    "$WORK_ROOT" \
    "$TMP_ROOT" \
    "$CACHE_ROOT"

  if [[ ! -d "$RAW_ROOT" ]]; then
    echo "preflight: missing RAW_ROOT: $RAW_ROOT" >&2
    exit 2
  fi

  if [[ ! -d "$STEPS_DIR" ]]; then
    echo "preflight: missing STEPS_DIR: $STEPS_DIR" >&2
    exit 2
  fi

  if [[ ! -r "$RAW_ROOT" ]]; then
    echo "preflight: RAW_ROOT not readable: $RAW_ROOT" >&2
    exit 2
  fi

  touch "${RUNTIME_ROOT}/.preflight_write_test" && rm -f "${RUNTIME_ROOT}/.preflight_write_test"
  touch "${LOG_ROOT}/.preflight_write_test" && rm -f "${LOG_ROOT}/.preflight_write_test"
  touch "${WORK_ROOT}/.preflight_write_test" && rm -f "${WORK_ROOT}/.preflight_write_test"
  touch "${TMP_ROOT}/.preflight_write_test" && rm -f "${TMP_ROOT}/.preflight_write_test"
  touch "${CACHE_ROOT}/.preflight_write_test" && rm -f "${CACHE_ROOT}/.preflight_write_test"
  touch "${DATA_ROOT}/.preflight_write_test" && rm -f "${DATA_ROOT}/.preflight_write_test"

  if ! command -v flock >/dev/null 2>&1; then
    echo "preflight: missing command: flock" >&2
    exit 2
  fi

  if ! command -v find >/dev/null 2>&1; then
    echo "preflight: missing command: find" >&2
    exit 2
  fi

  if ! command -v lftp >/dev/null 2>&1; then
    echo "preflight: missing command: lftp" >&2
    exit 2
  fi

  if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "preflight: missing command: sqlite3" >&2
    exit 2
  fi

  if [[ -n "${DB_PATH:-}" ]]; then
    mkdir -p "$(dirname "$DB_PATH")"
    touch "$DB_PATH"
  fi

  echo "preflight: ok"
}
