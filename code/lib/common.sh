#!/usr/bin/env bash
set -euo pipefail

ts() {
  date +'%F %T'
}

mklog() {
  local log_dir="$1" prefix="$2"
  mkdir -p "$log_dir"
  echo "${log_dir%/}/${prefix}_$(date +'%Y-%m-%d_%H-%M-%S').log"
}

log() {
  : "${LOG:?LOG is not set}"
  echo "[$(ts)] $*" | tee -a "$LOG"
}

die() {
  local rc="${2:-20}"
  log "ERROR: $1"
  exit "$rc"
}

acquire_lock() {
  local lockfile="$1" fd="$2"
  mkdir -p "$(dirname "$lockfile")"
  eval "exec ${fd}>\"${lockfile}\""
  if ! flock -n "${fd}"; then
    return 1
  fi
  return 0
}
