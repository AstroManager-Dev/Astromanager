# backup.sh: SQLite-Datei und SQL-Dump im Projekt-Backup

Stand: 2026-03-17

## Zweck
Das Projekt-Backup enthält jetzt zusätzlich SQLite-Backup-Artefakte der Pipeline-Datenbank.

## Enthaltene DB-Dateien im ZIP
Unter `db/` werden – falls `pipeline.db` gefunden wird – abgelegt:

- `db/pipeline.db`
- `db/pipeline.backup.db`
- `db/pipeline.sql`

## Suchreihenfolge der Datenbank
1. `DB_PATH` aus `env/.env`, falls vorhanden
2. `RUNTIME_ROOT/pipeline.db` aus `env/.env`
3. `${PROJECT_ROOT}/runtime/pipeline.db`
4. `${PROJECT_ROOT}/compose/runtime/pipeline.db`
5. `/runtime/pipeline.db`
6. `/opt/astro/runtime/pipeline.db`

## Backup-Metadaten
`_backups/astromanager/LATEST_BACKUP.txt` enthält zusätzlich:

- `sqlite_source=...`

## Hinweise
- `config/tailscale/` bleibt vollständig ausgeschlossen
- Bilddateien wie JPG/PNG/WEBP bleiben im Projekt-Backup enthalten
- FITS-Dateien bleiben im No-Media-Backup weiter ausgeschlossen
