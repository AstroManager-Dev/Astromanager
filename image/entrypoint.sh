#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] starting astromanager runner"
echo "[entrypoint] RAW_ROOT=${RAW_ROOT:-}"
echo "[entrypoint] DATA_ROOT=${DATA_ROOT:-}"
echo "[entrypoint] RUNTIME_ROOT=${RUNTIME_ROOT:-}"
echo "[entrypoint] LOG_ROOT=${LOG_ROOT:-}"
echo "[entrypoint] WORK_ROOT=${WORK_ROOT:-}"
echo "[entrypoint] TMP_ROOT=${TMP_ROOT:-}"
echo "[entrypoint] CACHE_ROOT=${CACHE_ROOT:-}"
echo "[entrypoint] CONFIG_ROOT=${CONFIG_ROOT:-}"
echo "[entrypoint] DB_PATH=${DB_PATH:-}"

for d in \
  "${RAW_ROOT:-}" \
  "${DATA_ROOT:-}" \
  "${RUNTIME_ROOT:-}" \
  "${LOG_ROOT:-}" \
  "${WORK_ROOT:-}" \
  "${TMP_ROOT:-}" \
  "${CACHE_ROOT:-}" \
  "${CONFIG_ROOT:-}"
do
  if [ -z "$d" ]; then
    echo "[entrypoint] ERROR: empty required directory variable" >&2
    exit 20
  fi
  if [ ! -d "$d" ]; then
    echo "[entrypoint] ERROR: missing directory: $d" >&2
    exit 21
  fi
done

touch "${RUNTIME_ROOT}/.write_test" && rm -f "${RUNTIME_ROOT}/.write_test"
touch "${LOG_ROOT}/.write_test" && rm -f "${LOG_ROOT}/.write_test"
touch "${WORK_ROOT}/.write_test" && rm -f "${WORK_ROOT}/.write_test"
touch "${TMP_ROOT}/.write_test" && rm -f "${TMP_ROOT}/.write_test"
touch "${CACHE_ROOT}/.write_test" && rm -f "${CACHE_ROOT}/.write_test"

mkdir -p "$(dirname "${DB_PATH}")"

echo "[entrypoint] mount check ok"
exec "$@"
