# Settings Header und Info-Modul neu aufgebaut

## Ziel
Die dedizierte Settings-Seite bekommt wieder einen klaren Header-Block, mehr Luft unter der Button-Auswahl und einen eigenen Info-Bereich mit dem bestehenden Changelog-Modul.

## Umsetzung
- eigener Header-Block als `pages/settings/_header.html`
- Segment-Buttons in `_settings_page.html` beibehalten, aber mit zusätzlichem Spacer darunter
- neuer Info-Bereich als `pages/settings/_info.html`
- bestehendes Patch-Log-Modul aus `pages/program_info/_patch_log_collapse.html` dort eingebunden
- jede Settings-Sektion lädt wieder ein eigenes leeres Bereichstemplate, das nur Module einbindet
- vorhandene Dummy-Inhalte in neue Modul-Teildateien ausgelagert

## Struktur
- `pages/settings/_devices.html`, `_sources.html`, `_display.html`, `_system.html` sind jetzt Shell-Templates
- die eigentlichen Platzhalter-Module liegen in den Unterordnern `pages/settings/devices/`, `sources/`, `display/`, `system/`

## Hinweis
Keine DB-Änderungen, keine Fachlogik-Erweiterung, kein Final-Merge.
