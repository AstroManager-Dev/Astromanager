# Overview Module Patch – 2026-03-16

Basis ist der reale Backup-Stand `astromanager_v0.4.015_2026-03-16_16-45-22.zip`.

## Ziel
- Overview modularisieren
- Status-Hero wieder ergänzen
- Hero kompakt und technisch statt groß und verspielt aufbauen
- experimentelle LED-Laufkante und Prozentanzeige vorerst wieder entfernen
- Textpositionen im Hero klarer und kompakter anordnen
- Schnellaktionen größer und im gleichen HUD-System wie der Hero ausführen
- workflow-spezifische Metriken nur dynamisch und optional anzeigen

## Struktur
- `code/web/templates/pages/_overview.html`
- `code/web/templates/pages/overview/_status_hero.html`
- `code/web/templates/pages/overview/_actions.html`
- `code/web/templates/pages/overview/_response.html`
- `code/web/templates/pages/overview/_recent_run_item.html`
- `code/web/templates/pages/overview/_recent_runs.html`
- `code/web/templates/pages/overview/_recent_runs_admin.html`

## Verhalten
- Hero priorisiert laufenden Run, sonst letzten Run
- Hero zeigt nur workflow-unabhängige Kerndaten immer an
- Metrik-Zeile wird nur eingeblendet, wenn für den jeweiligen Workflow passende Daten vorliegen
- LED-Rahmenfortschritt und Prozentkapsel bleiben vorerst deaktiviert und können später wiederkommen
- Overview zeigt 5 letzte Runs, Admin erweitert
