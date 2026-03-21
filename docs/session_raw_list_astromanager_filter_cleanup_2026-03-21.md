# Session RAW list Astromanager filter cleanup — 2026-03-21

## Änderung
- Astromanager-RAW-Liste blendet bekannte technische Hilfsdateien jetzt explizit aus.
- `stacked_thumbnail.*` wird hart ausgeschlossen, auch wenn `stacked*` generell erlaubt ist.
- TIFF/TIF-Dateien bekommen für den Viewer eine serverseitige Raster-Preview als WEBP, damit die Detailansicht und das Vollbild nicht vom Browser-TIFF-Support abhängen.

## Ausgeblendet
- `shotsInfo.json`
- `stacked_thumbnail.*`
- `img_reference.*`
- `img_stacked_counter.*`
- weitere reine Thumbnail-Hilfsdateien

## Sichtbar
- `stacked*.fits`
- `stacked*.jpg`
- `stacked*.jpeg`
- `stacked*.png`
- `stacked*.tif`
- `stacked*.tiff`
- `stacked*.webp`

## Viewer
- TIFF/TIF nutzt in der Detailansicht jetzt eine serverseitig erzeugte WEBP-Preview.
- Originaldatei bleibt über den Download-Endpunkt unverändert verfügbar.
