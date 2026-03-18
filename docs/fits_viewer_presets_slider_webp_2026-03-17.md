# FITS Viewer: Presets in DB, Slider und WebP

## Umgesetzt
- neue DB-Tabelle `fits_viewer_presets` als zentrale Quelle für Viewer-System-Presets
- System-Presets `Auto`, `Neutral`, `Nebula`, `Moon / Planet`, `Linear` per Migration angelegt
- Preset-Auswahl im RAW-FITS-Viewer von Chip-Liste auf Dropdown umgestellt
- Black, White und Gamma auf Slider mit Live-Wertanzeige umgebaut
- Viewer-Renderparameter werden serverseitig konsistent auf Stretch, Black, White und Gamma angewendet
- Vorschau-Endpunkte liefern jetzt WebP aus; bei fehlender WebP-Unterstützung im Pillow-Build wird intern auf PNG zurückgefallen

## Architektur
- `fits_viewer_presets` enthält nur kleine, direkt nutzbare Viewer-Fachwerte
- `auto` bleibt ein System-Preset-Key und wird im Backend über RAW-Metadaten auf ein konkretes Preset aufgelöst
- manuelle Slider-/Select-Werte dürfen ein Preset übersteuern; wenn die Werte nicht mehr exakt zum Preset passen, zeigt die UI `Custom`

## Dry-Run / Testlauf
- Migration lokal auf temporäre SQLite-DB anwenden
- prüfen, dass `fits_viewer_presets` angelegt und befüllt wird
- `enrich_raw_file_viewer_context(...)` mit Beispiel-RAWs für FITS/Mono/Color simulieren
- prüfen, dass `selected_preset_key`, Slider-Werte und WebP-URLs korrekt erzeugt werden
