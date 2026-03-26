# TIFF DZI + OpenSeadragon Viewer

Stand: 2026-03-21

## Ziel
TIFF-Dateien sollen im Vollbild nicht mehr nur als statische Raster-Preview laufen, sondern als Deep-Zoom-Quelle über libvips und OpenSeadragon.

## Architektur
- Normalansicht bleibt serverseitige Raster-Preview.
- Vollbild für TIFF nutzt eine DZI-Quelle.
- DZI und Tile-Ordner werden unter `/cache/web/tiff_dzi/` erzeugt.
- Erzeugung erfolgt per `vips dzsave`.
- Frontend nutzt OpenSeadragon bereits für Vollbild-Viewer.

## Routen
- `/media/raw-file-tiff-dzi/<id>.dzi`
- `/media/raw-file-tiff-tiles/<id>/<tile>`
- bestehende Kompatibilitätsroute `/media/raw-file-image-preview/<id>.<fmt>` bleibt auf Raster-Preview gemappt.

## Build
Im App-Image wird `libvips-tools` installiert. `pyvips` wird nicht benötigt.

## Viewer-Regel
- FITS bleibt der fachlich bessere Primärviewer.
- TIFF ist Raster-/Exportviewer in der Seitenansicht.
- TIFF nutzt im Vollbild DZI + OSD für besseres Zoom/Pan-Verhalten.
