# Dateitypspezifische Viewer-Auswahl mit Vollbild-Overlay

## Ziel
- keine Tab-Umschaltung zwischen Datei/FITS
- Viewer wird automatisch nach Dateityp gewählt
- FITS-Dateien starten direkt im FITS-Viewer-Modus
- Zoom nur im Vollbild
- Vollbild-Overlay mit fixem Schließen-Button oben rechts

## Umsetzung
- `fits_viewer.py` setzt `viewer_type`, `fullscreen_media_url` und den Default-Modus jetzt dateitypspezifisch
- FITS nutzt weiter die bestehende serverseitige Preview-Render-Pipeline
- JPEG/PNG und andere Browser-Bilder nutzen die normale `media_url`
- `_viewer_module.html` zeigt nur noch einen kompakten Vorschau-Block und den Button für Vollbild
- Render-Einstellungen für FITS liegen in einem eingeklappten `details`-Block
- Vollbild wird über `raw_file_viewer_fullscreen.js` gesteuert
- OpenSeadragon wird nur im Vollbild und nur für FITS initialisiert

## Build
- `image/Dockerfile` lädt `openseadragon.min.js` beim App-Build lokal nach `/app/web/static/vendor/openseadragon/`
- Laufzeit bleibt lokal ohne CDN im Browser

## Dry-Run
1. Patch einspielen
2. `./compose/rebuild_app.sh`
3. RAW-Detail mit FITS öffnen
4. Prüfen: kompakte Vorschau in der Seite, Vollbild mit Zoom/Pan und fixem Schließen-Button
5. JPEG/PNG prüfen: kompakte Vorschau + Vollbild ohne FITS-Regler
