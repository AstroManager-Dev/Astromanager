# OpenSeadragon lokal für FITS-Preview

## Ziel

Der bisherige serverseitige FITS-Preview bleibt erhalten. Für Zoom und Pan wird lokal eingebundenes OpenSeadragon auf dieselbe Preview-URL gelegt.

## Umsetzung

- lokale OSD-Einbindung über `code/web/static/vendor/openseadragon/openseadragon.min.js`
- Download im App-Image-Build nach `/app/web/static/vendor/openseadragon/`
- keine DB-Änderung
- kein Eingriff in `app.py`
- bestehende FITS-Presets, Debayer- und Stretch-Parameter bleiben unverändert
- Session-Detail und RAW-Detail nutzen dasselbe Viewer-Modul

## Viewer-Verhalten

- Pinch-Zoom und Pan auf Mobile
- Scroll-/Doppelklick-Zoom auf Desktop
- eigene Toolbar statt OSD-Standard-Buttons
- Fallback-Bild unter dem OSD-Viewer bleibt sichtbar

## Zusatzfix

`fits_viewer.py` behandelt `raw_file["session"]` jetzt robust, falls dort `None` statt eines Dicts ankommt.

## Dry-Run

Nach dem Einspielen:

```bash
cd /home/pi/docker/astromanager
./compose/rebuild_app.sh
docker exec -it astromanager-web sh -lc 'ls -lah /app/web/static/vendor/openseadragon/openseadragon.min.js'
```

Dann RAW-Detail mit FITS-Ansicht öffnen und prüfen:

- Viewer sichtbar
- Pinch-Zoom/Pan aktiv
- Preset-Änderung lädt neue Preview
- Session-Detail nutzt denselben Viewer
