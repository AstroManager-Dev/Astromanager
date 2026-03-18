# FITS-Viewer V2 – Session-Modul, Render-Cache und Auto-Presets

## Stand

Patch auf Basis `0.4.023`.

## Inhalt

- serverseitiger FITS-Render-Cache unter `CACHE_ROOT/fits_previews`
- Histogramm-basierte Preview-Pipeline statt rein statischer Vorschau
- Background Neutralization
- White Balance (`off`, `soft`, `auto`)
- Green Balance (`off`, `soft`, `medium`)
- Presets:
  - Auto
  - Neutral
  - Nebula
  - Linear
  - Moon/Planet
- Auto-Preset-Auswahl anhand von Metadaten:
  - Mond/Sonne/Planeten -> `moon_planet`
  - Duo-/Dual-/Ha-/OIII-/Narrowband-Filter oder lange Belichtung -> `nebula`
  - sonst `neutral`
- Session-Ansicht lädt den FITS-Viewer direkt im Bildmodul
- RAW-Liste bleibt weiter ohne FITS-Listenrender

## Betroffene Dateien

- `code/web/functions/common.py`
- `code/web/functions/fits_viewer.py`
- `code/web/functions/gallery.py`
- `code/web/app.py`
- `code/web/templates/pages/raw_file_detail/_viewer_module.html`
- `code/web/templates/pages/session_detail/_fits_panel.html`
- `code/web/templates/pages/session_detail/_image_module.html`
- `code/web/static/css/modules/30_fits_viewer.css`

## Testhinweise

1. Web neu bauen
2. RAW-FITS-Detailseite öffnen
3. Session-Detailseite öffnen und auf `FITS` schalten
4. prüfen, ob Vorschau deutlich dunkler/neutraler als vorher wirkt
5. zweite Anforderung derselben Parameter sollte aus dem Cache kommen

