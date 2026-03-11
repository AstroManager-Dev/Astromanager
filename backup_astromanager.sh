#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%F_%H-%M-%S)"
TODAY="$(date +%F)"
SRC="/home/pi/docker/astromanager"

VERSION_FILE="${SRC}/VERSION"
SCHEMA_VERSION_FILE="${SRC}/SCHEMA_VERSION"
CHANGELOG_FILE="${SRC}/CHANGELOG.md"
UNRELEASED_FILE="${SRC}/CHANGELOG.unreleased.md"

if [ -f "$VERSION_FILE" ]; then
  APP_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
else
  APP_VERSION="0.0.000"
fi

if [ -f "$SCHEMA_VERSION_FILE" ]; then
  SCHEMA_VERSION="$(tr -d '[:space:]' < "$SCHEMA_VERSION_FILE")"
else
  SCHEMA_VERSION="0"
fi

BACKUP_BASE="${SRC}/_backups"
DEST_ROOT="${BACKUP_BASE}/astromanager"
STAGE_DIR="${DEST_ROOT}/_stage_astromanager_${TS}"
ZIP_NAME="astromanager_v${APP_VERSION}_${TS}.zip"
ZIP_PATH="${DEST_ROOT}/${ZIP_NAME}"

mkdir -p "$DEST_ROOT"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

rsync -aHAX --delete-excluded \
  --exclude '_backups/' \
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

if command -v docker >/dev/null 2>&1; then
  docker ps -a > "${STAGE_DIR}/docker_ps_a.txt" 2>/dev/null || true
  docker images > "${STAGE_DIR}/docker_images.txt" 2>/dev/null || true
  if [ -f "${SRC}/compose/docker-compose.yml" ]; then
    docker compose -f "${SRC}/compose/docker-compose.yml" config > "${STAGE_DIR}/docker_compose_resolved.yml" 2>/dev/null || true
  fi
fi

# Im Backup aus CHANGELOG.md + CHANGELOG.unreleased.md eine vollständige CHANGELOG.md bauen.
# Die Live-Dateien im Projekt bleiben unverändert.
TMP_CHANGELOG="$(mktemp)"
{
  echo "# Changelog"
  echo
  echo "## ${TODAY}  Version: ${APP_VERSION}"
  echo "- Backup-Stand erzeugt"
  echo "- Projektversion: ${APP_VERSION}"
  echo "- Schema-Version: ${SCHEMA_VERSION}"

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
Quelle: ${SRC}
Zielordner: ${DEST_ROOT}
ZIP: ${ZIP_PATH}

Enthalten:
- compose/
- code/
- config/
- env/
- image/
- scripts/
- Dokumentation/
- VERSION
- SCHEMA_VERSION
- zusammengeführtes CHANGELOG.md
- kleine DB-/Projektdateien
- Docker-Zustandsinfos, falls verfügbar

Ausgeschlossen:
- _backups/
- FITS
- Bilder/Video
- raw/data/work/cache/tmp/logs
- Astronomy/Burst/Normal_Photos/Panoramas/Videos/Catalog/DarkPool
- CHANGELOG.unreleased.md im finalen Backup
INFO

cd "$DEST_ROOT"
rm -f "$ZIP_PATH"
zip -r "$ZIP_PATH" "$(basename "$STAGE_DIR")"

rm -rf "$STAGE_DIR"

echo "ZIP-Backup fertig: $ZIP_PATH"
