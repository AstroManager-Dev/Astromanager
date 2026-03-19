# Session-Detail Objekt-Infocards 2026-03-19

## Basis
- Echter Master-Stand: 0.4.050 Patch-Backup
- Session-Detail bleibt als gemeinsames Modul für alle Session-Typen bestehen

## Struktur
- `app.py` bleibt im Session-Detail nur Route + Datenaufbereitung + Render-Aufruf
- Objektbezogene Hero-Zusammenfassung ist nach `code/web/functions/session_detail.py` ausgelagert
- eigene Template-Dateien für die kleinen Objekt-Infocards:
  - Mond
  - Sonne
  - Deep Sky
  - Planet

## UI
- Eyebrow im Titelblock von `Session` auf `Details` umgestellt
- kompakte Objekt-Infocard direkt im Hero oberhalb des Bildmoduls ergänzt
- Mondkarte zeigt Phase, Mondalter, Beleuchtung und Distanz

## Technik
- kein eigenes komplettes Session-Template pro Objektklasse
- nur objektspezifische Hero-Infocard pro Typ
- Template-Iteration läuft über `session.object_info_card_items`, damit kein Jinja-Konflikt mit `dict.items()` entsteht
