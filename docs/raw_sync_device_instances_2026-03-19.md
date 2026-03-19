# RAW-Sync auf Device-Instances umgestellt

## Stand

Dieser Patch baut den RAW-Sync von hart codierten Host/User/Pass-Werten auf DB-gestützte `device_instances` um.

## Umsetzung

- `device_instances` ist jetzt die Laufzeitquelle für:
  - Host
  - Port
  - Login
  - Timeout
  - Remote-Base-Dir (Override)
  - erlaubte Dateiendungen (Override)
- `device_sources` bleibt Template-Ebene für:
  - Protokoll
  - Root-Pattern
  - Default-Remote-Base-Dir
  - Default-Extensions
- `astroctl raw sync` verarbeitet standardmäßig alle aktiven Device-Instances nacheinander.
- `--source-key` bleibt als Filter auf Template-Ebene erhalten.

## RAW-Dateitypen

Der Remote-Scanner berücksichtigt jetzt die aus DB geladenen erlaubten Endungen.
Damit können pro Quelle bzw. Instanz neben FITS auch z. B. PNG, JPEG, JSON, TIF und TIFF synchronisiert werden.

## Workflow-Fixes

Zusätzlich wurden die bekannten Fehler im Workflow behoben:

- `0030_plan_from_db.sh` nutzt jetzt korrekt `PYTHONPATH`
- `0040_transfer_files.sh` ist auf `step_run()` umgestellt
- `0040_transfer_files.sh` nutzt direkt `astromanager.raw.fetch_sync`
- `9999_trigger_index.sh` ist auf `step_run()` umgestellt und liest `fetch_result.json` korrekt
- `astroctl raw sync --dry-run` und `--source-key` werden korrekt an den Workflow durchgereicht

## Nächster Ausbau

- gezielte Auswahl einzelner Device-Instances per CLI
- UI-Formulare für Device-Instances
- Verbindungstest pro Instanz
