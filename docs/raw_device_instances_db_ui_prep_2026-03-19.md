# RAW Sync Vorbereitung: Device-Instances und Source-Defaults

Stand: 2026-03-19

## Ziel dieser Stufe

Diese Stufe zieht die bisher hart codierten RAW-Sync-Verbindungsdaten aus dem Code in die Datenbank und bereitet die Settings-UI auf echte Geräteinstanzen vor.

Diese Stufe enthält bewusst noch **keinen** kompletten RAW-Sync-Umbau auf Device-Instances. Sie schafft die Grundlage dafür.

## Datenmodell

### device_sources erweitert
Neue Default-Felder pro Quelltyp:
- `remote_base_dir`
- `allowed_extensions`

Damit liegen Modell-Defaults künftig direkt beim Source-Template.

### Neue Tabelle `device_instances`
Neue reale Geräteinstanzen mit:
- `instance_key`
- `display_name`
- `source_id`
- `connection_kind`
- `host`
- `port`
- `auth_mode`
- `username`
- `password_text`
- `timeout_seconds`
- optionale Overrides für Root und Extensions
- Aktiv-/Default-Status

## Seed-Stand

Für den aktuellen Bestand wird eine erste aktive Instanz angelegt:
- `instance_key = dwarflab_dwarf3`
- `display_name = DWARF 3`
- Host/FTP-Defaults entsprechend dem bisherigen Code-Stand

## UI

Der Settings-Bereich `sources` zeigt jetzt:
- echte Source-Templates aus `device_sources`
- echte Device-Instances aus `device_instances`

Die UI ist in dieser Stufe read-only und dient als saubere Sicht- und Prüfgrundlage vor dem nächsten Schritt mit Formularen und Sync-Umbau.

## Nächster Schritt

Im nächsten Patch wird der RAW-Sync selbst auf `device_instances` umgestellt, sodass aktive Geräteinstanzen nacheinander abgearbeitet werden können.
