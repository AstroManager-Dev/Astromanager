#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/pi/docker/astromanager"
VERSION_FILE="${PROJECT_ROOT}/VERSION"
UNRELEASED_FILE="${PROJECT_ROOT}/CHANGELOG.unreleased.md"
CHANGELOG_FILE="${PROJECT_ROOT}/CHANGELOG.md"
BACKUP_SCRIPT="${PROJECT_ROOT}/backup.sh"

if [ $# -lt 1 ]; then
  echo "Nutzung: ./bump_minor.sh \"Änderung am Skript\""
  exit 1
fi

CHANGE_TEXT="$*"
STAMP="$(date +'%F %H:%M:%S')"
TODAY="$(date +'%F')"

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

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"

NEW_LINE="${NEW_VERSION} | ${STAMP} | ${CHANGE_TEXT}"
TMP_UNRELEASED="$(mktemp)"

{
  printf '%s\n' "$NEW_LINE"
  if [ -f "$UNRELEASED_FILE" ]; then
    cat "$UNRELEASED_FILE"
  fi
} > "$TMP_UNRELEASED"

mv "$TMP_UNRELEASED" "$UNRELEASED_FILE"

TMP_CHANGELOG="$(mktemp)"
{
  if [ -f "$CHANGELOG_FILE" ]; then
    cat "$CHANGELOG_FILE"
  else
    echo "# Changelog"
    echo
  fi
} > "$TMP_CHANGELOG"

if ! grep -q '^# Changelog' "$TMP_CHANGELOG"; then
  {
    echo "# Changelog"
    echo
    cat "$TMP_CHANGELOG"
  } > "${TMP_CHANGELOG}.new"
  mv "${TMP_CHANGELOG}.new" "$TMP_CHANGELOG"
fi

TMP_RELEASE_BLOCK="$(mktemp)"
{
  echo "## ${NEW_VERSION} - ${TODAY}"
  echo "- ${CHANGE_TEXT}"
  echo
} > "$TMP_RELEASE_BLOCK"

awk -v block_file="$TMP_RELEASE_BLOCK" '
  BEGIN {
    while ((getline line < block_file) > 0) {
      block = block line "\n"
    }
    close(block_file)
  }
  NR == 1 {
    print
    next
  }
  NR == 2 {
    if ($0 == "") {
      print
      printf "%s", block
      next
    }
  }
  NR == 2 && $0 != "" {
    printf "%s", block
  }
  { print }
' "$TMP_CHANGELOG" > "${TMP_CHANGELOG}.new"

mv "${TMP_CHANGELOG}.new" "$CHANGELOG_FILE"
rm -f "$TMP_CHANGELOG" "$TMP_RELEASE_BLOCK"

echo "Minor-Version erhöht: $CURRENT_VERSION -> $NEW_VERSION"
echo "CHANGELOG.unreleased.md ergänzt."
echo "CHANGELOG.md ergänzt."

if [ ! -f "$BACKUP_SCRIPT" ]; then
  echo "Fehler: Backup-Skript fehlt: $BACKUP_SCRIPT"
  exit 1
fi

if [ ! -x "$BACKUP_SCRIPT" ]; then
  echo "Fehler: Backup-Skript ist nicht ausführbar: $BACKUP_SCRIPT"
  exit 1
fi

echo "Starte Backup-Skript: $BACKUP_SCRIPT --backup --label minor"
if "$BACKUP_SCRIPT" --backup --label minor; then
  echo "Minor-Bump inkl. Backup abgeschlossen."
else
  BACKUP_RC=$?
  echo "Warnung: Backup-Skript ist fehlgeschlagen (Exit-Code: $BACKUP_RC)."
  echo "Der Minor-Bump wurde trotzdem durchgeführt."
fi

if [ "${ASTROMANAGER_GIT_PUSH:-1}" = "1" ]; then
  if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"

    if [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "HEAD" ]; then
      git -C "$PROJECT_ROOT" reset -- _backups config/tailscale 2>/dev/null || true

      git -C "$PROJECT_ROOT" add -A . \
        ':(exclude)_backups' \
        ':(exclude)config/tailscale' \
        ':(exclude)backup.sh' \
        ':(exclude)backup_astromanager_nomedia_zip.sh' \
        ':(exclude)backup_astromanager.sh.legacy.disabled' \
        ':(exclude)scripts/release/bump_patch.sh' \
        ':(exclude)scripts/release/bump_minor.sh'

      if ! git -C "$PROJECT_ROOT" diff --cached --quiet; then
        GIT_COMMIT_MSG="release: bump minor to ${NEW_VERSION} - ${CHANGE_TEXT}"
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
