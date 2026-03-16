#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${DB_PATH:-/runtime/pipeline.db}"
BACKUP_DIR="${DB_BACKUP_DIR:-/runtime/db_backups}"
SQLITE_BIN="${SQLITE_BIN:-sqlite3}"

SAFETY_BACKUP_LATEST="${BACKUP_DIR}/pipeline_pre_restore_latest.sqlite3"
UNDO_MARKER_FILE="${BACKUP_DIR}/pipeline_pre_restore_latest.source.txt"

RESET_SCRIPT="${RESET_SCRIPT:-/app/bin/reset_db_except_never_reset.py}"
RESET_VACUUM=0
ASSUME_YES=0

mkdir -p "$BACKUP_DIR"

usage() {
  cat <<USAGE
Verwendung:
  db_backup_manager.sh
  db_backup_manager.sh --backup
  db_backup_manager.sh --list
  db_backup_manager.sh --pick-restore
  db_backup_manager.sh --restore --file /runtime/db_backups/pipeline_YYYY-MM-DD_HH-MM-SS.sqlite3 [--y]
  db_backup_manager.sh --undo-last-restore [--y]
  db_backup_manager.sh --reset-db [--vacuum] [--y]
  db_backup_manager.sh --delete --file /runtime/db_backups/pipeline_YYYY-MM-DD_HH-MM-SS.sqlite3 [--y]
  db_backup_manager.sh --pick-delete [--y]

Optionen:
  --backup              Erstellt ein neues DB-Backup
  --list                Listet vorhandene reguläre Backups auf
  --pick-restore        Zeigt Backups an und fragt interaktiv nach einer Auswahl zum Restore
  --restore --file X    Spielt ein ausgewähltes Backup zurück
  --undo-last-restore   Macht das letzte Restore über das zuletzt erzeugte Sicherheits-Backup rückgängig
  --reset-db            Führt den DB-Reset gemäß Never-Reset-Liste aus
  --delete --file X     Löscht ein ausgewähltes reguläres Backup
  --pick-delete         Zeigt Backups an und fragt interaktiv nach einer Auswahl zum Löschen
  --vacuum              Nur zusammen mit --reset-db: führt danach VACUUM aus
  --y                   Überspringt Sicherheitsabfragen
USAGE
}

log() {
  printf '[%s] %s\n' "$(date +'%F %T')" "$*"
}

die() {
  echo "FEHLER: $*" >&2
  exit 1
}

confirm_action() {
  local prompt="$1"
  if [[ "$ASSUME_YES" -eq 1 ]]; then
    return 0
  fi
  echo
  read -r -p "$prompt [ja/nein]: " confirm < /dev/tty
  [[ "$confirm" == "ja" ]]
}

pause_return() {
  echo
  read -r -p "Enter für zurück ..." _dummy < /dev/tty
}

require_db() {
  [[ -f "$DB_PATH" ]] || die "DB nicht gefunden: $DB_PATH"
}

timestamp() {
  date +%F_%H-%M-%S
}

regular_backup_glob() {
  find "$BACKUP_DIR" -maxdepth 1 -type f -name 'pipeline_*.sqlite3' \
    ! -name 'pipeline_pre_restore_latest.sqlite3' \
    ! -name 'pipeline_before_undo_*.sqlite3' | sort -r
}

load_backup_array() {
  mapfile -t BACKUP_FILES < <(regular_backup_glob)
}

print_backup_list() {
  local title="${1:-Verfügbare Backups}"
  load_backup_array

  echo
  echo "$title"
  echo "----------------------------------------"

  if [[ "${#BACKUP_FILES[@]}" -eq 0 ]]; then
    echo "Keine regulären Backups gefunden in $BACKUP_DIR"
    echo "0) Zurück"
    return 1
  fi

  local i=1
  local file
  for file in "${BACKUP_FILES[@]}"; do
    printf '%d) %s | %s\n' \
      "$i" \
      "$(basename "$file")" \
      "$(du -h "$file" | awk '{print $1}')"
    i=$((i + 1))
  done
  echo "0) Zurück"
  return 0
}

select_backup_from_list() {
  local mode="${1:-restore}"
  local title="Verfügbare Backups"
  local selection

  if [[ "$mode" == "restore" ]]; then
    title="Verfügbare Backups zum Restore"
  elif [[ "$mode" == "delete" ]]; then
    title="Verfügbare Backups zum Löschen"
  fi

  while true; do
    print_backup_list "$title" || {
      echo
      read -r -p "Bitte Nummer eingeben (0 = zurück): " selection < /dev/tty
      [[ "$selection" == "0" ]] && return 1
      echo "Ungültige Auswahl."
      continue
    }

    echo
    read -r -p "Bitte Nummer eingeben (0 = zurück): " selection < /dev/tty

    [[ "$selection" =~ ^[0-9]+$ ]] || {
      echo "Ungültige Auswahl."
      continue
    }

    if [[ "$selection" == "0" ]]; then
      return 1
    fi

    (( selection >= 1 && selection <= ${#BACKUP_FILES[@]} )) || {
      echo "Auswahl außerhalb des gültigen Bereichs."
      continue
    }

    SELECTED_BACKUP="${BACKUP_FILES[$((selection - 1))]}"
    return 0
  done
}

create_backup() {
  require_db
  local ts backup_path
  ts="$(timestamp)"
  backup_path="${BACKUP_DIR}/pipeline_${ts}.sqlite3"

  log "Erzeuge Backup"
  log "DB_PATH=$DB_PATH"
  log "BACKUP_FILE=$backup_path"

  "$SQLITE_BIN" "$DB_PATH" ".backup '$backup_path'"

  [[ -s "$backup_path" ]] || die "Backup wurde nicht korrekt erzeugt: $backup_path"
  log "OK Backup erstellt: $backup_path"
}

create_safety_backup_latest() {
  require_db
  log "Erzeuge Sicherheits-Backup vor Restore"
  rm -f "$SAFETY_BACKUP_LATEST"

  "$SQLITE_BIN" "$DB_PATH" ".backup '$SAFETY_BACKUP_LATEST'"

  [[ -s "$SAFETY_BACKUP_LATEST" ]] || die "Sicherheits-Backup konnte nicht erzeugt werden: $SAFETY_BACKUP_LATEST"
  log "OK Sicherheits-Backup aktualisiert: $SAFETY_BACKUP_LATEST"
}

restore_from_file() {
  local source_backup="$1"
  [[ -n "$source_backup" ]] || die "Kein Restore-File angegeben"
  [[ -f "$source_backup" ]] || die "Backup-Datei nicht gefunden: $source_backup"

  if ! confirm_action "Restore wirklich ausführen von $(basename "$source_backup")?"; then
    log "Restore abgebrochen"
    return 0
  fi

  create_safety_backup_latest
  printf '%s\n' "$source_backup" > "$UNDO_MARKER_FILE"

  local tmp_restore="${DB_PATH}.restore_tmp"
  rm -f "$tmp_restore"
  cp -f "$source_backup" "$tmp_restore"
  [[ -s "$tmp_restore" ]] || die "Temporäre Restore-Datei konnte nicht erzeugt werden: $tmp_restore"

  mv -f "$tmp_restore" "$DB_PATH"
  log "OK Restore abgeschlossen"
  log "Quelle: $source_backup"
  log "Undo-Backup: $SAFETY_BACKUP_LATEST"
}

undo_last_restore() {
  [[ -f "$SAFETY_BACKUP_LATEST" ]] || die "Kein Undo-Backup vorhanden: $SAFETY_BACKUP_LATEST"

  if ! confirm_action "Letztes Restore wirklich rückgängig machen?"; then
    log "Undo abgebrochen"
    return 0
  fi

  local current_backup="${BACKUP_DIR}/pipeline_before_undo_$(timestamp).sqlite3"

  if [[ -f "$DB_PATH" ]]; then
    log "Sichere aktuellen DB-Stand vor Undo"
    "$SQLITE_BIN" "$DB_PATH" ".backup '$current_backup'"
    [[ -s "$current_backup" ]] || die "Aktueller Stand vor Undo konnte nicht gesichert werden: $current_backup"
    log "OK Aktueller Stand gesichert: $current_backup"
  fi

  local tmp_restore="${DB_PATH}.undo_tmp"
  rm -f "$tmp_restore"
  cp -f "$SAFETY_BACKUP_LATEST" "$tmp_restore"
  [[ -s "$tmp_restore" ]] || die "Undo-Datei konnte nicht vorbereitet werden: $tmp_restore"

  mv -f "$tmp_restore" "$DB_PATH"
  log "OK Letztes Restore rückgängig gemacht"
  if [[ -f "$UNDO_MARKER_FILE" ]]; then
    log "Ursprünglich eingespielte Datei war: $(cat "$UNDO_MARKER_FILE")"
  fi
}

reset_db_except_keep() {
  [[ -f "$RESET_SCRIPT" ]] || die "Reset-Skript nicht gefunden: $RESET_SCRIPT"

  if ! confirm_action "DB-Reset wirklich ausführen?"; then
    log "DB-Reset abgebrochen"
    return 0
  fi

  log "Erzeuge normales Backup vor DB-Reset"
  create_backup

  if [[ "$RESET_VACUUM" -eq 1 ]]; then
    log "Starte DB-Reset mit VACUUM"
    python3 "$RESET_SCRIPT" --vacuum
  else
    log "Starte DB-Reset"
    python3 "$RESET_SCRIPT"
  fi

  log "OK DB-Reset abgeschlossen"
}

delete_backup_file() {
  local file="$1"
  [[ -n "$file" ]] || die "Keine Backup-Datei angegeben"
  [[ -f "$file" ]] || die "Backup-Datei nicht gefunden: $file"

  if ! confirm_action "Backup wirklich löschen: $(basename "$file")?"; then
    log "Löschen abgebrochen"
    return 0
  fi

  rm -f "$file"
  log "OK Backup gelöscht: $file"
}

menu_backup_create() {
  create_backup
  pause_return
}

menu_backup_list() {
  print_backup_list "Verfügbare Backups" || true
  pause_return
}

menu_backup_restore() {
  if ! select_backup_from_list restore; then
    return 0
  fi
  restore_from_file "$SELECTED_BACKUP"
  pause_return
}

menu_undo_restore() {
  undo_last_restore
  pause_return
}

menu_reset_db() {
  reset_db_except_keep
  pause_return
}

menu_backup_delete() {
  if ! select_backup_from_list delete; then
    return 0
  fi
  delete_backup_file "$SELECTED_BACKUP"
  pause_return
}

interactive_menu() {
  while true; do
    echo
    echo "DB Backup Manager"
    echo "1) Backup erstellen"
    echo "2) Backups auflisten"
    echo "3) Backup zurückspielen"
    echo "4) Letztes Restore rückgängig machen"
    echo "5) DB resetten (außer Never-Reset-Tabellen)"
    echo "6) Backup löschen"
    echo "0) Beenden"
    echo

    read -r -p "Auswahl: " choice < /dev/tty

    case "$choice" in
      1) menu_backup_create ;;
      2) menu_backup_list ;;
      3) menu_backup_restore ;;
      4) menu_undo_restore ;;
      5) menu_reset_db ;;
      6) menu_backup_delete ;;
      0) exit 0 ;;
      *) echo "Ungültige Auswahl." ;;
    esac
  done
}

MODE=""
RESTORE_FILE=""
DELETE_FILE=""
SELECTED_BACKUP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)
      MODE="backup"
      shift
      ;;
    --restore)
      MODE="restore"
      shift
      ;;
    --pick-restore)
      MODE="pick_restore"
      shift
      ;;
    --delete)
      MODE="delete"
      shift
      ;;
    --pick-delete)
      MODE="pick_delete"
      shift
      ;;
    --file)
      if [[ "${MODE:-}" == "delete" ]]; then
        DELETE_FILE="${2:-}"
      else
        RESTORE_FILE="${2:-}"
      fi
      shift 2
      ;;
    --undo-last-restore)
      MODE="undo"
      shift
      ;;
    --reset-db)
      MODE="reset"
      shift
      ;;
    --vacuum)
      RESET_VACUUM=1
      shift
      ;;
    --y)
      ASSUME_YES=1
      shift
      ;;
    --list)
      MODE="list"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unbekanntes Argument: $1"
      ;;
  esac
done

case "$MODE" in
  "")
    interactive_menu
    ;;
  backup)
    create_backup
    ;;
  restore)
    [[ -n "$RESTORE_FILE" ]] || die "--restore benötigt zusätzlich --file"
    restore_from_file "$RESTORE_FILE"
    ;;
  pick_restore)
    if select_backup_from_list restore; then
      restore_from_file "$SELECTED_BACKUP"
    else
      log "Restore-Auswahl abgebrochen"
    fi
    ;;
  delete)
    [[ -n "$DELETE_FILE" ]] || die "--delete benötigt zusätzlich --file"
    delete_backup_file "$DELETE_FILE"
    ;;
  pick_delete)
    if select_backup_from_list delete; then
      delete_backup_file "$SELECTED_BACKUP"
    else
      log "Lösch-Auswahl abgebrochen"
    fi
    ;;
  undo)
    undo_last_restore
    ;;
  reset)
    reset_db_except_keep
    ;;
  list)
    print_backup_list "Verfügbare Backups" || true
    ;;
  *)
    die "Ungültiger Modus"
    ;;
esac
