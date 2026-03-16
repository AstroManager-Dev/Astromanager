# Target Detail Header Reorder 2026-03-16

- Target-Detail-Header auf gewünschte Reihenfolge umgestellt: Name -> Bild -> Meta -> Sessions
- `_target_header_card.html` auf bestehende `target-card`/`hud-info-shell`-Styles umgestellt
- Roh wirkende Header-Struktur mit undefinierten `hud-target-card`-Klassen entfernt
- Meta sauber als Fact-Module für Typ, Sessions, RA, DEC und Distanz angeordnet
- Bottom-Navigation-Aktivierung auf Target-Detailseiten indirekt mitgefixt, weil `app.js` wegen `openMenuBtn` statt `openMenuBtns` vorher in einen JS-Fehler lief und dadurch die aktive Tab-Markierung nicht auf `targets` umgestellt wurde
