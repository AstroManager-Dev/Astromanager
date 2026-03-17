# CSS-Modul-Loader und RAW-Listen-CSS Patch

## Problem

`app.css` wurde durch einen Einzelpatch überschrieben. Dadurch war die Haupt-CSS-Datei zu fragil für kleine UI-Korrekturen.

## Umsetzung

- `base.html` lädt weiterhin zentral `app.css`
- zusätzliche CSS-Dateien aus `code/web/static/css/modules/*.css` werden automatisch alphabetisch nachgeladen
- neue RAW-Listen-Stile liegen jetzt getrennt in `code/web/static/css/modules/20_raw_list.css`
- der versehentlich direkt in `app.css` angehängte RAW-Listen-Block wurde wieder entfernt

## Nutzen

- `app.css` bleibt die stabile Basisdatei
- kleine Layout-Erweiterungen können als modulare CSS-Dateien ergänzt werden
- spätere UI-Patches überschreiben nicht mehr versehentlich die Haupt-CSS
