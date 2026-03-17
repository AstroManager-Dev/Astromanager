# Settings Info Tab und Minor-Log

## Stand
- Settings hatte den oberen Header wieder inline statt als Modul.
- Der Info-Bereich lag unten außerhalb der Segment-Navigation.
- Minor-Log fehlte im Settings-Info-Bereich.
- Unter den Segment-Buttons war der Abstand zu knapp.

## Umsetzung
- Settings-Header als eigenes Modul `_header.html` aufgebaut.
- Neues Settings-Modul `_info.html` ergänzt.
- `Info` als eigener Segment-Button in die obere Auswahl aufgenommen.
- Im Info-Modul werden jetzt Versionskopf, Minor-Log und Patch-Log eingebunden.
- Zusätzlicher Abstand unter der Segment-Auswahl ergänzt.

## Betroffene Dateien
- `code/web/templates/pages/_settings_page.html`
- `code/web/templates/pages/settings/_header.html`
- `code/web/templates/pages/settings/_info.html`
- `code/web/static/css/app.css`
