# Targets Intro + Target Resolver Modul

## Stand
- Analyse und Umsetzung auf Basis des normalen Backups `astromanager_v0.4.020_2026-03-17_09-25-12`
- DB-Inhalt nur aus dem im Backup enthaltenen SQL-Dump genutzt
- `target_final` / Final-Merge bleibt ausgeschlossen

## Umsetzung
- `code/web/templates/pages/_targets.html`
  - wieder an `includes/_page_intro.html` angebunden
- `code/web/templates/pages/_target_detail.html`
  - Resolver-Modul unten sauber eingebunden
  - doppelte/inkonsistente Resolver-Includes bereinigt
- `code/web/functions/targets.py`
  - Resolver-Feldliste auf reine Resolverdaten reduziert
  - Final-Merge weiterhin nicht Teil der Anzeige

## Dry-Run
- `/#targets` öffnen und oberen Bereich mit `/#gallery` vergleichen
- `/targets/<id>` öffnen und unten Resolver-Datenblöcke prüfen
- erwartet: ein Block pro Resolver-Tabelle mit vorhandenen Rohdaten
