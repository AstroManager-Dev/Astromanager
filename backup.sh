#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

PROJECT_ROOT="${ASTROMANAGER_PROJECT_ROOT:-$SCRIPT_DIR}"
if [ ! -f "${PROJECT_ROOT}/VERSION" ] && [ -d "/home/pi/docker/astromanager" ]; then
  PROJECT_ROOT="/home/pi/docker/astromanager"
fi

BACKUP_BASE="${ASTROMANAGER_BACKUP_BASE:-${PROJECT_ROOT}/_backups}"
DEST_ROOT="${ASTROMANAGER_BACKUP_DEST_ROOT:-${BACKUP_BASE}/astromanager}"
ARCHIVE_DIR="${ASTROMANAGER_BACKUP_ARCHIVE_DIR:-${DEST_ROOT}/Archiv}"

VERSION_FILE="${PROJECT_ROOT}/VERSION"
SCHEMA_VERSION_FILE="${PROJECT_ROOT}/SCHEMA_VERSION"
CHANGELOG_FILE="${PROJECT_ROOT}/CHANGELOG.md"
UNRELEASED_FILE="${PROJECT_ROOT}/CHANGELOG.unreleased.md"
SOURCE_ENV_FILE="${PROJECT_ROOT}/env/.env"

KEEP_ROOT_BACKUPS="${ASTROMANAGER_KEEP_ROOT_BACKUPS:-1}"
CUSTOM_NAME=""
CUSTOM_LABEL=""
RESTORE_ZIP=""
MODE=""
STAGE_ROOT=""
FOUND_DB=""

usage() {
  cat <<'USAGE'
Usage:
  backup.sh --backup [--name ZIP_NAME] [--label LABEL] [--keep-root N]
  backup.sh --restore ZIP_PATH

Beispiele:
  backup.sh --backup
  backup.sh --backup --label patch
  backup.sh --backup --name astromanager_manual_2026-03-17.zip
  backup.sh --restore /home/pi/docker/astromanager/_backups/astromanager/astromanager_v0.4.024_2026-03-17_21-49-40.zip
USAGE
}

cleanup_stage_root() {
  if [ -n "${STAGE_ROOT:-}" ] && [ -d "${STAGE_ROOT:-}" ]; then
    rm -rf "$STAGE_ROOT"
  fi
}
trap cleanup_stage_root EXIT

safe_slug() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9._-]+/_/g; s/^_+//; s/_+$//; s/_{2,}/_/g'
}

build_zip_name() {
  local version="$1"
  local ts="$2"
  local label="$3"

  if [ -n "$CUSTOM_NAME" ]; then
    case "$CUSTOM_NAME" in
      *.zip) printf '%s\n' "$CUSTOM_NAME" ;;
      *) printf '%s.zip\n' "$CUSTOM_NAME" ;;
    esac
    return
  fi

  local base="astromanager_v${version}"
  if [ -n "$label" ]; then
    base="${base}_$(safe_slug "$label")"
  fi
  printf '%s_%s.zip\n' "$base" "$ts"
}

load_source_env() {
  if [ -f "$SOURCE_ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$SOURCE_ENV_FILE"
    set +a
  fi
}

find_pipeline_db() {
  local candidates=()

  if [ -n "${DB_PATH:-}" ]; then
    candidates+=("$DB_PATH")
  fi

  if [ -n "${RUNTIME_ROOT:-}" ]; then
    candidates+=("${RUNTIME_ROOT}/pipeline.db")
  fi

  candidates+=(
    "${PROJECT_ROOT}/runtime/pipeline.db"
    "${PROJECT_ROOT}/compose/runtime/pipeline.db"
    "/runtime/pipeline.db"
    "/opt/astro/runtime/pipeline.db"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

add_sqlite_backup_artifacts() {
  local db_path="$1"
  [ -n "$db_path" ] || return 0
  [ -f "$db_path" ] || return 0

  mkdir -p "${STAGE_ROOT}/db"
  cp "$db_path" "${STAGE_ROOT}/db/pipeline.db"

  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$db_path" ".backup '${STAGE_ROOT}/db/pipeline.backup.db'"
    sqlite3 "$db_path" ".dump" > "${STAGE_ROOT}/db/pipeline.sql"
  fi
}

write_latest_backup_info() {
  local zip_path="$1"
  local created_at="$2"
  local app_version="$3"
  local schema_version="$4"

  cat > "${DEST_ROOT}/LATEST_BACKUP.txt" <<INFO
latest_zip=${zip_path}
created_at=${created_at}
project_version=${app_version}
schema_version=${schema_version}
backup_label=${CUSTOM_LABEL}
sqlite_source=${FOUND_DB}
INFO
}

while [ $# -gt 0 ]; do
  case "$1" in
    --backup)
      MODE="backup"
      ;;
    --restore)
      MODE="restore"
      shift
      [ $# -gt 0 ] || { echo "Fehler: --restore erwartet einen ZIP-Pfad"; exit 1; }
      RESTORE_ZIP="$1"
      ;;
    --name)
      shift
      [ $# -gt 0 ] || { echo "Fehler: --name erwartet einen Wert"; exit 1; }
      CUSTOM_NAME="$1"
      ;;
    --label)
      shift
      [ $# -gt 0 ] || { echo "Fehler: --label erwartet einen Wert"; exit 1; }
      CUSTOM_LABEL="$1"
      ;;
    --keep-root)
      shift
      [ $# -gt 0 ] || { echo "Fehler: --keep-root erwartet einen Wert"; exit 1; }
      KEEP_ROOT_BACKUPS="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Fehler: Unbekannte Option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

[ -n "$MODE" ] || { usage; exit 1; }

if ! [[ "$KEEP_ROOT_BACKUPS" =~ ^[0-9]+$ ]]; then
  echo "Fehler: --keep-root muss eine nichtnegative ganze Zahl sein"
  exit 1
fi

do_backup() {
  local ts today app_version schema_version zip_name zip_path tmp_changelog
  ts="$(date +%F_%H-%M-%S)"
  today="$(date +%F)"

  if [ -f "$VERSION_FILE" ]; then
    app_version="$(tr -d '[:space:]' < "$VERSION_FILE")"
  else
    app_version="0.0.000"
  fi
  [ -n "$app_version" ] || app_version="0.0.000"

  if [ -f "$SCHEMA_VERSION_FILE" ]; then
    schema_version="$(tr -d '[:space:]' < "$SCHEMA_VERSION_FILE")"
  else
    schema_version="0"
  fi

  load_source_env
  FOUND_DB="$(find_pipeline_db || true)"

  mkdir -p "$DEST_ROOT" "$ARCHIVE_DIR"

  zip_name="$(build_zip_name "$app_version" "$ts" "$CUSTOM_LABEL")"
  zip_path="${DEST_ROOT}/${zip_name}"
  STAGE_ROOT="$(mktemp -d "/tmp/astromanager_backup_stage_${ts}_XXXXXX")"

  rsync -aHAX --delete-excluded \
    --exclude '_backups/' \
    --exclude 'config/tailscale/***' \
    --exclude 'compose/.env' \
    --exclude 'compose/secrets/' \
    --exclude 'code/raw/' \
    --exclude 'code/data/' \
    --exclude 'code/work/' \
    --exclude 'code/cache/' \
    --exclude 'code/tmp/' \
    --exclude 'code/logs/' \
    --exclude 'compose/raw/' \
    --exclude 'compose/data/' \
    --exclude 'compose/work/' \
    --exclude 'compose/cache/' \
    --exclude 'compose/tmp/' \
    --exclude 'compose/logs/' \
    --exclude '**/*.fits' \
    --exclude '**/*.fit' \
    --exclude '**/*.fts' \
    --exclude '**/*.mp4' \
    --exclude '**/*.mkv' \
    --exclude '**/*.avi' \
    --exclude '**/Astronomy/' \
    --exclude '**/Burst/' \
    --exclude '**/Normal_Photos/' \
    --exclude '**/Panoramas/' \
    --exclude '**/Videos/' \
    --exclude '**/Catalog/' \
    --exclude '**/DarkPool/' \
    --exclude '**/__pycache__/' \
    --exclude '**/.pytest_cache/' \
    --exclude '**/.mypy_cache/' \
    --exclude '**/.cache/' \
    --exclude '**/node_modules/' \
    --exclude '**/.git/' \
    "$PROJECT_ROOT/" "$STAGE_ROOT/"

  if command -v docker >/dev/null 2>&1; then
    docker ps -a > "${STAGE_ROOT}/docker_ps_a.txt" 2>/dev/null || true
    docker images > "${STAGE_ROOT}/docker_images.txt" 2>/dev/null || true
    if [ -f "${PROJECT_ROOT}/compose/docker-compose.yml" ]; then
      docker compose -f "${PROJECT_ROOT}/compose/docker-compose.yml" config > "${STAGE_ROOT}/docker_compose_resolved.yml" 2>/dev/null || true
    fi
  fi

  add_sqlite_backup_artifacts "$FOUND_DB"

  tmp_changelog="$(mktemp)"
  {
    echo "# Changelog"
    echo
    echo "## ${today}  Version: ${app_version}"
    echo "- Backup-Stand erzeugt"
    echo "- Projektversion: ${app_version}"
    echo "- Schema-Version: ${schema_version}"
    if [ -n "$CUSTOM_LABEL" ]; then
      echo "- Backup-Label: ${CUSTOM_LABEL}"
    fi
    if [ -n "$FOUND_DB" ]; then
      echo "- SQLite-Quelle: ${FOUND_DB}"
    else
      echo "- SQLite-Quelle: nicht gefunden"
    fi

    if [ -f "$UNRELEASED_FILE" ] && [ -s "$UNRELEASED_FILE" ]; then
      while IFS= read -r line; do
        [ -z "$line" ] && continue
        desc="$(printf '%s\n' "$line" | awk -F' \\| ' '
          NF >= 3 {
            text = $3
            for (i = 4; i <= NF; i++) text = text " | " $i
            print text
          }
        ')"
        if [ -n "$desc" ]; then
          printf -- '- %s\n' "$desc"
        else
          printf -- '- %s\n' "$line"
        fi
      done < "$UNRELEASED_FILE"
    elif [ -f "$CHANGELOG_FILE" ] && [ -s "$CHANGELOG_FILE" ]; then
      awk '
        /^## / { if (printed++) exit; next }
        /^- / { print }
      ' "$CHANGELOG_FILE"
    else
      echo "- Kein Changelog gefunden"
    fi
  } > "$tmp_changelog"

  cp "$tmp_changelog" "${STAGE_ROOT}/CHANGELOG.snapshot.md"
  rm -f "$tmp_changelog"

  rm -f "$zip_path"
  (
    cd "$STAGE_ROOT"
    zip -qr "$zip_path" .
  )

  mapfile -t root_zips < <(find "$DEST_ROOT" -maxdepth 1 -type f -name '*.zip' | sort)
  local root_count="${#root_zips[@]}"
  if [ "$root_count" -gt "$KEEP_ROOT_BACKUPS" ]; then
    local move_count=$((root_count - KEEP_ROOT_BACKUPS))
    for ((i=0; i<move_count; i++)); do
      mv "${root_zips[$i]}" "$ARCHIVE_DIR/"
    done
  fi

  local active_count
  active_count="$(find "$DEST_ROOT" -maxdepth 1 -type f -name '*.zip' | wc -l | tr -d '[:space:]')"

  write_latest_backup_info "$zip_path" "$ts" "$app_version" "$schema_version"

  echo "ZIP-Backup fertig: $zip_path"
  echo "Aktive ZIPs im Hauptordner: $active_count"
  echo "Ältere ZIPs liegen in: $ARCHIVE_DIR"

  cleanup_stage_root
  STAGE_ROOT=""
}

do_restore() {
  [ -n "$RESTORE_ZIP" ] || { echo "Fehler: Kein Restore-ZIP angegeben"; exit 1; }
  [ -f "$RESTORE_ZIP" ] || { echo "Fehler: ZIP nicht gefunden: $RESTORE_ZIP"; exit 1; }

  STAGE_ROOT="$(mktemp -d "/tmp/astromanager_restore_stage_XXXXXX")"

  unzip -q "$RESTORE_ZIP" -d "$STAGE_ROOT"

  echo "Restore-Quelle: $RESTORE_ZIP"
  echo "Restore-Ziel:   $PROJECT_ROOT"
  echo
  echo "Es werden nur die im ZIP enthaltenen Dateien/Unterordner zurückgespielt und überschrieben."
  echo "Nicht im ZIP enthaltene Projektdateien bleiben unverändert."
  echo

  rsync -aHAX \
    "$STAGE_ROOT/" "$PROJECT_ROOT/"

  echo "Restore abgeschlossen: $RESTORE_ZIP -> $PROJECT_ROOT"

  cleanup_stage_root
  STAGE_ROOT=""
}

case "$MODE" in
  backup)
    do_backup
    ;;
  restore)
    do_restore
    ;;
esac
