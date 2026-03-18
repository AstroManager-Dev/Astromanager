# FITS Viewer: Presets, Auto White Balance und Green Balance

## Stand
Patch auf Basis von `v0.4.023`.

## Inhalt
- FITS-Viewer um Presets erweitert: Neutral, Nebula, Linear, Moon/Planet
- Auto White Balance als wählbarer Modus ergänzt
- optionale Green Balance (`off` / `soft`) ergänzt
- Preview-Rendering nimmt jetzt Stretch, Black, White, Gamma, White Balance und Green Balance aus der URL an
- kompakte Preset-Buttons in der Detailansicht ergänzt
- neue Modul-CSS `static/css/modules/30_fits_viewer.css`

## Wirkung
- allgemeine Vorschau kann neutraler gerendert werden
- Duo-Band-/Nebelmaterial kann mit Nebula-Preset bewusst wärmer bleiben
- Mond/Planet kann als ruhiger Mono-/Linear-Preset geöffnet werden
- nur Detailseite betroffen, RAW-Liste bleibt FITS-preview-frei
