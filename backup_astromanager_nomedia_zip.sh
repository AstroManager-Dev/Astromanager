#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

FALLBACK_SRC="/home/pi/docker/astromanager"
FALLBACK_BACKUP_BASE="${FALLBACK_SRC}/_backups"
FALLBACK_DEST_ROOT="${FALLBACK_BACKUP_BASE}/astromanager"
FALLBACK_ARCHIVE_DIR="${FALLBACK_DEST_ROOT}/Archiv"
FALLBACK_ZIP_BASENAME="astromanager_backup"

SRC="${ASTROMANAGER_BACKUP_SRC:-$SCRIPT_DIR}"
if [ ! -f "${SRC}/VERSION" ] && [ -d "$FALLBACK_SRC" ]; then
  SRC="$FALLBACK_SRC"
fi

TS="$(date +%F_%H-%M-%S)"
TODAY="$(date +%F)"

VERSION_FILE="${SRC}/VERSION"
SCHEMA_VERSION_FILE="${SRC}/SCHEMA_VERSION"
CHANGELOG_FILE="${SRC}/CHANGELOG.md"
UNRELEASED_FILE="${SRC}/CHANGELOG.unreleased.md"

BACKUP_BASE="${ASTROMANAGER_BACKUP_BASE:-${SRC}/_backups}"
DEST_ROOT="${ASTROMANAGER_BACKUP_DEST_ROOT:-${BACKUP_BASE}/astromanager}"
ARCHIVE_DIR="${ASTROMANAGER_BACKUP_ARCHIVE_DIR:-${DEST_ROOT}/Archiv}"

if [ -z "$BACKUP_BASE" ]; then
  BACKUP_BASE="$FALLBACK_BACKUP_BASE"
fi
if [ -z "$DEST_ROOT" ]; then
  DEST_ROOT="$FALLBACK_DEST_ROOT"
fi
if [ -z "$ARCHIVE_DIR" ]; then
  ARCHIVE_DIR="$FALLBACK_ARCHIVE_DIR"
fi

CUSTOM_NAME=""
CUSTOM_LABEL=""
KEEP_ROOT_BACKUPS=1

usage() {
  cat <<USAGE
Usage:
  $(basename "$0") [--name ZIP_NAME] [--label LABEL] [--keep-root N]

Optionen:
  --name ZIP_NAME   Exakter ZIP-Dateiname, optional mit oder ohne .zip
  --label LABEL     Zusatzlabel für den Dateinamen, z. B. patch, minor, manual
  --keep-root N     Wie viele aktuelle ZIPs direkt im Hauptordner bleiben sollen (Standard: 1)

Beispiele:
  $(basename "$0")
  $(basename "$0") --label patch
  $(basename "$0") --name astromanager_v0.2.030_patch_2026-03-11_10-30-00.zip
USAGE
}

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
    local name="$CUSTOM_NAME"
    case "$name" in
      *.zip) ;;
      *) name="${name}.zip" ;;
    esac
    printf '%s\n' "$name"
    return
  fi

  local base=""
  if [ -n "$version" ] && [ "$version" != "0.0.000" ]; then
    base="astromanager_v${version}"
  else
    base="${ASTROMANAGER_BACKUP_FALLBACK_BASENAME:-$FALLBACK_ZIP_BASENAME}"
  fi

  if [ -n "$label" ]; then
    base="${base}_$(safe_slug "$label")"
  fi

  if [ -z "$base" ]; then
    base="$FALLBACK_ZIP_BASENAME"
  fi

  printf '%s_%s.zip\n' "$base" "$ts"
}

while [ $# -gt 0 ]; do
  case "$1" in
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

if ! [[ "$KEEP_ROOT_BACKUPS" =~ ^[0-9]+$ ]]; then
  echo "Fehler: --keep-root muss eine nichtnegative ganze Zahl sein"
  exit 1
fi

if [ -f "$VERSION_FILE" ]; then
  APP_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
else
  APP_VERSION="0.0.000"
fi

if [ -z "$APP_VERSION" ]; then
  APP_VERSION="0.0.000"
fi

if [ -f "$SCHEMA_VERSION_FILE" ]; then
  SCHEMA_VERSION="$(tr -d '[:space:]' < "$SCHEMA_VERSION_FILE")"
else
  SCHEMA_VERSION="0"
fi

ZIP_NAME="$(build_zip_name "$APP_VERSION" "$TS" "$CUSTOM_LABEL")"
STAGE_DIR="${DEST_ROOT}/_stage_astromanager_${TS}"
ZIP_PATH="${DEST_ROOT}/${ZIP_NAME}"

mkdir -p "$DEST_ROOT" "$ARCHIVE_DIR"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

rsync -aHAX --delete-excluded \
  --exclude '_backups/' \
  --exclude 'compose/.env' \
  --exclude 'compose/secrets/' \
  --exclude 'config/tailscale/' \
  --exclude 'config/tailscale/**' \
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
  --exclude '**/*.png' \
  --exclude '**/*.jpg' \
  --exclude '**/*.jpeg' \
  --exclude '**/*.tif' \
  --exclude '**/*.tiff' \
  --exclude '**/*.webp' \
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
  "$SRC/" "$STAGE_DIR/"

DB_FILE_CANDIDATES=(
  "${SRC}/runtime/pipeline.db"
  "${SRC}/code/runtime/pipeline.db"
  "/runtime/pipeline.db"
  "/app/runtime/pipeline.db"
)

FOUND_DB=""
for candidate in "${DB_FILE_CANDIDATES[@]}"; do
  if [ -f "$candidate" ]; then
    FOUND_DB="$candidate"
    break
  fi
done

if [ -n "$FOUND_DB" ]; then
  mkdir -p "${STAGE_DIR}/runtime"

  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$FOUND_DB" ".backup '${STAGE_DIR}/runtime/pipeline.db'"
    sqlite3 "$FOUND_DB" ".schema" > "${STAGE_DIR}/runtime/pipeline.schema.sql" || true
    sqlite3 "$FOUND_DB" ".dump" > "${STAGE_DIR}/runtime/pipeline.dump.sql" || true
    echo "SQLite-DB gesichert: $FOUND_DB"
  else
    cp -a "$FOUND_DB" "${STAGE_DIR}/runtime/pipeline.db"
    echo "Hinweis: sqlite3 nicht gefunden, DB-Datei nur kopiert: $FOUND_DB"
  fi
else
  echo "Hinweis: Keine pipeline.db gefunden, DB-Dump übersprungen."
fi

if command -v docker >/dev/null 2>&1; then
  docker ps -a > "${STAGE_DIR}/docker_ps_a.txt" 2>/dev/null || true
  docker images > "${STAGE_DIR}/docker_images.txt" 2>/dev/null || true
  if [ -f "${SRC}/compose/docker-compose.yml" ]; then
    docker compose -f "${SRC}/compose/docker-compose.yml" config > "${STAGE_DIR}/docker_compose_resolved.yml" 2>/dev/null || true
  fi
fi

TMP_CHANGELOG="$(mktemp)"
{
  echo "# Changelog"
  echo
  echo "## ${TODAY}  Version: ${APP_VERSION}"
  echo "- Backup-Stand erzeugt"
  echo "- Projektversion: ${APP_VERSION}"
  echo "- Schema-Version: ${SCHEMA_VERSION}"

  if [ -n "$CUSTOM_LABEL" ]; then
    echo "- Backup-Label: ${CUSTOM_LABEL}"
  fi

  if [ -n "$FOUND_DB" ]; then
    echo "- SQLite-DB gesichert: ${FOUND_DB}"
  else
    echo "- SQLite-DB nicht gefunden"
  fi

  if [ -f "$UNRELEASED_FILE" ] && [ -s "$UNRELEASED_FILE" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      DESC="$(printf '%s\n' "$line" | awk -F' \\| ' '
        NF >= 3 {
          desc = $3
          for (i = 4; i <= NF; i++) {
            desc = desc " | " $i
          }
          print desc
        }
      ')"
      if [ -n "$DESC" ]; then
        printf -- '- %s\n' "$DESC"
      else
        printf -- '- %s\n' "$line"
      fi
    done < "$UNRELEASED_FILE"
  fi

  echo

  if [ -f "$CHANGELOG_FILE" ]; then
    awk 'NR > 1 { print }' "$CHANGELOG_FILE"
  fi
} > "$TMP_CHANGELOG"

cp "$TMP_CHANGELOG" "${STAGE_DIR}/CHANGELOG.md"
rm -f "$TMP_CHANGELOG"
rm -f "${STAGE_DIR}/CHANGELOG.unreleased.md"

cat > "${STAGE_DIR}/BACKUP_INFO.txt" <<INFO
Backup: AstroManager ohne Mediendaten
Erstellt: ${TS}
Projektversion: ${APP_VERSION}
Schema-Version: ${SCHEMA_VERSION}
Backup-Label: ${CUSTOM_LABEL}
Quelle: ${SRC}
Zielordner: ${DEST_ROOT}
Archivordner: ${ARCHIVE_DIR}
ZIP: ${ZIP_PATH}
SQLite-Quelle: ${FOUND_DB}

Enthalten:
- compose/
- code/
- config/
- env/
- image/
- scripts/
- Dokumentation/
- runtime/pipeline.db (falls gefunden)
- runtime/pipeline.schema.sql (falls sqlite3 vorhanden)
- runtime/pipeline.dump.sql (falls sqlite3 vorhanden)
- VERSION
- SCHEMA_VERSION
- zusammengeführtes CHANGELOG.md
- kleine DB-/Projektdateien
- Docker-Zustandsinfos, falls verfügbar

Ausgeschlossen:
- _backups/
- config/tailscale/
- FITS
- Bilder/Video
- raw/data/work/cache/tmp/logs
- Astronomy/Burst/Normal_Photos/Panoramas/Videos/Catalog/DarkPool
- CHANGELOG.unreleased.md im finalen Backup
INFO

cd "$STAGE_DIR"
rm -f "$ZIP_PATH"
zip -r "$ZIP_PATH" . >/dev/null

rm -rf "$STAGE_DIR"

cleanup_old_root_backups() {
  local keep="$1"
  mapfile -t root_zips < <(find "$DEST_ROOT" -maxdepth 1 -type f -name 'astromanager*.zip' -printf '%T@|%p\n' | sort -rn)

  local count=0
  for entry in "${root_zips[@]}"; do
    local file="${entry#*|}"
    count=$((count + 1))
    if [ "$count" -le "$keep" ]; then
      continue
    fi
    mv -f "$file" "${ARCHIVE_DIR}/"
  done
}

cleanup_old_root_backups "$KEEP_ROOT_BACKUPS"

LATEST_FILE="${DEST_ROOT}/LATEST_BACKUP.txt"
cat > "$LATEST_FILE" <<INFO
latest_zip=${ZIP_PATH}
created_at=${TS}
project_version=${APP_VERSION}
schema_version=${SCHEMA_VERSION}
backup_label=${CUSTOM_LABEL}
sqlite_source=${FOUND_DB}
INFO

echo "ZIP-Backup fertig: $ZIP_PATH"
echo "ZIP-Inhalt liegt direkt im ZIP-Root."
echo "Aktive ZIPs im Hauptordner: $KEEP_ROOT_BACKUPS"
echo "Ältere ZIPs liegen in: $ARCHIVE_DIR"
