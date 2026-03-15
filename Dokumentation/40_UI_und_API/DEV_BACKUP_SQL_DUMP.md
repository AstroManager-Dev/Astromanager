# Dev-Backup mit SQL-Dump

## Zweck

Beim Erstellen eines Dev-Core-Backups wird automatisch ein aktueller SQL-Dump aus `/runtime/pipeline.db` erzeugt.

## Lokaler Ablageort

Der letzte integrierte Dump wird immer hier überschrieben:

- `local/backup_sql/pipeline_latest.sql`

Dieser Ordner ist rein lokal und darf nicht nach GitHub gelangen.

## Verhalten

- Vor jedem Core-Backup wird `pipeline_latest.sql` neu erstellt.
- Der Dump wird anschließend zusätzlich in das Core-Backup-ZIP übernommen.
- Das Backup bricht mit Fehler ab, wenn
  - die Datenbank fehlt,
  - der Dump leer ist,
  - oder der Dump nicht im erzeugten ZIP enthalten ist.

## Backup-Inhalt

Zusätzlich zu `code/`, `scripts/`, `VERSION`, `SCHEMA_VERSION`, `CHANGELOG.md` und `CHANGELOG.unreleased.md` enthält das Backup:

- `local/backup_sql/pipeline_latest.sql`
