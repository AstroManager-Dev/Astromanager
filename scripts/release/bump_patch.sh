#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/pi/docker/astromanager"
VERSION_FILE="${PROJECT_ROOT}/VERSION"
UNRELEASED_FILE="${PROJECT_ROOT}/CHANGELOG.unreleased.md"
BACKUP_SCRIPT="${PROJECT_ROOT}/backup_astromanager_nomedia_zip.sh"

if [ $# -lt 1 ]; then
  echo "Nutzung: ./bump_patch.sh \"Änderung am Skript\""
  exit 1
fi

CHANGE_TEXT="$*"
STAMP="$(date +'%F %H:%M:%S')"

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
PATCH="${CURRENT_VERSION##*.}"

NEW_PATCH="$(printf '%03d' "$((10#$PATCH + 1))")"
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"

NEW_LINE="${NEW_VERSION} | ${STAMP} | ${CHANGE_TEXT}"
TMP_FILE="$(mktemp)"

{
  printf '%s\n' "$NEW_LINE"
  if [ -f "$UNRELEASED_FILE" ]; then
    cat "$UNRELEASED_FILE"
  fi
} > "$TMP_FILE"

mv "$TMP_FILE" "$UNRELEASED_FILE"

echo "Patch-Version erhöht: $CURRENT_VERSION -> $NEW_VERSION"
echo "CHANGELOG.unreleased.md ergänzt."

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

echo "Patch-Bump inkl. Backup abgeschlossen."

if [ "${ASTROMANAGER_GIT_PUSH:-1}" = "1" ]; then
  if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"

    if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "HEAD" ]; then
      git -C "$PROJECT_ROOT" add -A .

      if ! git -C "$PROJECT_ROOT" diff --cached --quiet; then
        GIT_COMMIT_MSG="release: bump patch to ${NEW_VERSION} - ${CHANGE_TEXT}"
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
