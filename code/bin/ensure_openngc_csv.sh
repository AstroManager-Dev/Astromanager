#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
source "$ROOT/lib/pipeline_env.sh"
source "$ROOT/lib/source_config.sh"

DB_PATH="${DB_PATH:-/runtime/pipeline.db}"
SQLITE_BIN="${SQLITE_BIN:-sqlite3}"

SOURCE_KEY="openngc_csv"
SOURCE_URL="${OPENNGC_CSV_URL}"
LOCAL_PATH="${OPENNGC_CSV_LOCAL}"
MAX_AGE_DAYS="${OPENNGC_MAX_AGE_DAYS:-30}"
TIMEOUT="${TARGET_RESOLVER_TIMEOUT:-20}"

log() {
  printf '[%s] ensure_openngc_csv: %s\n' "$(date +'%F %T')" "$*"
}

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

db_exec() {
  "$SQLITE_BIN" "$DB_PATH" "$1"
}

set_state() {
  local status="$1"
  local error_message="$2"
  local now url path expires_at
  now="$(date +'%F %T')"
  url="$(sql_escape "$SOURCE_URL")"
  path="$(sql_escape "$LOCAL_PATH")"
  error_message="$(sql_escape "$error_message")"
  expires_at="$(date -d "+${MAX_AGE_DAYS} days" +'%F %T')"

  db_exec "
  INSERT INTO external_source_state (
    source_key, source_url, local_path, status,
    last_checked_at, expires_at, error_message,
    created_at, updated_at
  )
  VALUES (
    '${SOURCE_KEY}', '${url}', '${path}', '${status}',
    '${now}', '${expires_at}', '${error_message}',
    datetime('now'), datetime('now')
  )
  ON CONFLICT(source_key) DO UPDATE SET
    source_url=excluded.source_url,
    local_path=excluded.local_path,
    status=excluded.status,
    last_checked_at=excluded.last_checked_at,
    expires_at=excluded.expires_at,
    error_message=excluded.error_message,
    updated_at=datetime('now');
  "
}

set_download_success() {
  local now url path expires_at
  now="$(date +'%F %T')"
  url="$(sql_escape "$SOURCE_URL")"
  path="$(sql_escape "$LOCAL_PATH")"
  expires_at="$(date -d "+${MAX_AGE_DAYS} days" +'%F %T')"

  db_exec "
  INSERT INTO external_source_state (
    source_key, source_url, local_path, status,
    last_checked_at, last_downloaded_at, expires_at, error_message,
    created_at, updated_at
  )
  VALUES (
    '${SOURCE_KEY}', '${url}', '${path}', 'ok',
    '${now}', '${now}', '${expires_at}', '',
    datetime('now'), datetime('now')
  )
  ON CONFLICT(source_key) DO UPDATE SET
    source_url=excluded.source_url,
    local_path=excluded.local_path,
    status='ok',
    last_checked_at=excluded.last_checked_at,
    last_downloaded_at=excluded.last_downloaded_at,
    expires_at=excluded.expires_at,
    error_message='',
    updated_at=datetime('now');
  "
}

get_expires_at() {
  db_exec "SELECT COALESCE(expires_at,'') FROM external_source_state WHERE source_key='${SOURCE_KEY}' LIMIT 1;"
}

is_expired() {
  local expires_at="$1"
  if [[ -z "$expires_at" ]]; then
    return 0
  fi
  local now_ts exp_ts
  now_ts="$(date +%s)"
  exp_ts="$(date -d "$expires_at" +%s 2>/dev/null || echo 0)"
  [[ "$exp_ts" -le "$now_ts" ]]
}

download_csv() {
  local tmp_file
  tmp_file="$(mktemp)"
  if curl -fsSL --connect-timeout "$TIMEOUT" --max-time "$((TIMEOUT * 3))" "$SOURCE_URL" -o "$tmp_file"; then
    mkdir -p "$(dirname "$LOCAL_PATH")"
    mv "$tmp_file" "$LOCAL_PATH"
    set_download_success
    log "downloaded fresh catalog to $LOCAL_PATH"
    return 0
  fi
  rm -f "$tmp_file"
  return 1
}

main() {
  mkdir -p "$(dirname "$LOCAL_PATH")"

  local have_local=0
  [[ -s "$LOCAL_PATH" ]] && have_local=1

  local expires_at
  expires_at="$(get_expires_at || true)"

  if [[ "$have_local" -eq 0 ]]; then
    log "local catalog missing, trying download"
    if download_csv; then
      exit 0
    fi
    set_state "error" "download failed and no local fallback available"
    log "download failed and no local fallback available"
    exit 1
  fi

  if is_expired "$expires_at"; then
    log "local catalog expired or unknown, trying refresh"
    if download_csv; then
      exit 0
    fi
    set_state "stale_local_fallback" "refresh failed, using existing local catalog"
    log "refresh failed, using existing local catalog at $LOCAL_PATH"
    exit 0
  fi

  set_state "ok" ""
  log "local catalog still valid at $LOCAL_PATH"
  exit 0
}

main "$@"
