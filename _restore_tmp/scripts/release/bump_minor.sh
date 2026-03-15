#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/pi/docker/astromanager"
VERSION_FILE="${PROJECT_ROOT}/VERSION"
CHANGELOG_FILE="${PROJECT_ROOT}/CHANGELOG.md"
UNRELEASED_FILE="${PROJECT_ROOT}/CHANGELOG.unreleased.md"

SCHEMA_DIR="${PROJECT_ROOT}/code/db/schema"
SCHEMA_FILE="${SCHEMA_DIR}/0001_current_baseline.sql"
MIGRATIONS_DIR="${PROJECT_ROOT}/code/db/migrations"

BACKUP_SCRIPT="${PROJECT_ROOT}/backup_astromanager_nomedia_zip.sh"

RUNNER_CONTAINER="astromanager-runner"
DB_PATH_IN_CONTAINER="/runtime/pipeline.db"

if [ $# -lt 1 ]; then
  echo "Nutzung: ./bump_minor.sh \"Release-Zusammenfassung\""
  exit 1
fi

RELEASE_SUMMARY="$*"
TODAY="$(date +%F)"

if [ ! -f "$VERSION_FILE" ]; then
  echo "Fehler: VERSION fehlt: $VERSION_FILE"
  exit 1
fi

CURRENT_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

if ! printf '%s\n' "$CURRENT_VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]{3}$'; then
  echo "Fehler: VERSION hat nicht das erwartete Format MAJOR.MINOR.PATCH mit 3-stelligem PATCH"
  echo "Aktuell: $CURRENT_VERSION"
  exit 1
fi

MAJOR="${CURRENT_VERSION%%.*}"
REST="${CURRENT_VERSION#*.}"
MINOR="${REST%%.*}"

NEW_MINOR="$((10#$MINOR + 1))"
NEW_VERSION="${MAJOR}.${NEW_MINOR}.000"

if [ ! -f "$CHANGELOG_FILE" ]; then
  cat > "$CHANGELOG_FILE" <<'EOT'
# Changelog
EOT
fi

RELEASE_BLOCK_FILE="$(mktemp)"
{
  printf '## %s  Version: %s\n' "$TODAY" "$NEW_VERSION"
  printf -- '- %s\n' "$RELEASE_SUMMARY"

  if [ -s "$UNRELEASED_FILE" ]; then
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
      fi
    done < "$UNRELEASED_FILE"
  fi

  printf '\n'
} > "$RELEASE_BLOCK_FILE"

TMP_CHANGELOG="$(mktemp)"
awk -v block_file="$RELEASE_BLOCK_FILE" '
BEGIN {
  inserted = 0
  while ((getline line < block_file) > 0) {
    block = block line "\n"
  }
  close(block_file)
}
{
  print $0
  if (!inserted && $0 == "# Changelog") {
    print ""
    printf "%s", block
    inserted = 1
  } else {
    print ""
  }
}
END {
  if (!inserted) {
    print "# Changelog"
    print ""
    printf "%s", block
  }
}
' "$CHANGELOG_FILE" > "$TMP_CHANGELOG"

awk '
BEGIN { blank = 0 }
{
  if ($0 == "") {
    if (blank == 0) print
    blank = 1
  } else {
    print
    blank = 0
  }
}
' "$TMP_CHANGELOG" > "${TMP_CHANGELOG}.clean"

mv "${TMP_CHANGELOG}.clean" "$CHANGELOG_FILE"
rm -f "$TMP_CHANGELOG" "$RELEASE_BLOCK_FILE"

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"
: > "$UNRELEASED_FILE"

echo "Minor-Version erhöht: $CURRENT_VERSION -> $NEW_VERSION"
echo "CHANGELOG.md vereinheitlicht, neueste Version steht oben."
echo "CHANGELOG.unreleased.md wurde geleert."

if ! docker ps --format '{{.Names}}' | grep -qx "$RUNNER_CONTAINER"; then
  echo "Fehler: Container läuft nicht: $RUNNER_CONTAINER"
  exit 1
fi

mkdir -p "$SCHEMA_DIR"

TMP_SCHEMA="$(mktemp)"
{
  printf 'PRAGMA foreign_keys=OFF;\n'
  printf 'BEGIN;\n\n'
  docker exec -i "$RUNNER_CONTAINER" sqlite3 "$DB_PATH_IN_CONTAINER" ".schema"
  printf '\nCOMMIT;\n'
  printf 'PRAGMA foreign_keys=ON;\n'
} > "$TMP_SCHEMA"

mv "$TMP_SCHEMA" "$SCHEMA_FILE"
echo "Aktuelles Baseline-Schema neu erzeugt: $SCHEMA_FILE"

if [ -d "$MIGRATIONS_DIR" ]; then
  find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name '*.sql' -delete
  echo "Migrations gelöscht: $MIGRATIONS_DIR"
else
  echo "Hinweis: Migrations-Verzeichnis nicht gefunden: $MIGRATIONS_DIR"
fi

if [ ! -f "$BACKUP_SCRIPT" ]; then
  echo "Fehler: Backup-Skript fehlt: $BACKUP_SCRIPT"
  exit 1
fi

if [ ! -x "$BACKUP_SCRIPT" ]; then
  echo "Fehler: Backup-Skript ist nicht ausführbar: $BACKUP_SCRIPT"
  exit 1
fi

echo "Starte Backup-Skript: $BACKUP_SCRIPT"
"$BACKUP_SCRIPT"

echo "Minor-Bump inkl. neuem Baseline-Schema, Migrations-Cleanup und Backup abgeschlossen."

if [ "${ASTROMANAGER_GIT_PUSH:-1}" = "1" ]; then
  if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"

    if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "HEAD" ]; then
      git -C "$PROJECT_ROOT" add -A .
      git -C "$PROJECT_ROOT" reset -- backup_astromanager_nomedia_zip.sh backup_astromanager.sh.legacy.disabled scripts/release/bump_patch.sh scripts/release/bump_minor.sh 2>/dev/null || true
      git -C "$PROJECT_ROOT" reset -- _backups 2>/dev/null || true

      if ! git -C "$PROJECT_ROOT" diff --cached --quiet; then
        GIT_COMMIT_MSG="release: bump minor to ${NEW_VERSION} - ${RELEASE_SUMMARY}"
        git -C "$PROJECT_ROOT" commit -m "$GIT_COMMIT_MSG"
        git -C "$PROJECT_ROOT" push origin "$CURRENT_BRANCH"
        echo "Git-Commit und Push abgeschlossen: $CURRENT_BRANCH"
      else
        echo "Hinweis: Keine Git-Änderungen zum Committen."
      fi
    else
      echo "Hinweis: Kein normaler Git-Branch erkannt, Push übersprungen."
    fi
  else
    echo "Hinweis: $PROJECT_ROOT ist kein Git-Repository, Git-Schritt übersprungen."
  fi
else
  echo "Hinweis: Git-Push per ASTROMANAGER_GIT_PUSH=0 deaktiviert."
fi
