# FITS Viewer Memmap Hotfix

## Problem

Bestimmte FITS-Dateien mit `BZERO`, `BSCALE` oder `BLANK` im Header ließen sich im Web-Viewer nicht rendern.

Astropy brach dabei mit folgendem Fehler ab:

- `ValueError: Cannot load a memory-mapped image: BZERO/BSCALE/BLANK header keywords present. Set memmap=False.`

Betroffen waren sowohl die Detailvorschau als auch die Thumbnail-Route des FITS-Viewers.

## Umsetzung

- FITS-Dateien werden im Viewer jetzt mit `memmap=False` geöffnet.
- Der Zugriff auf `hdu.data` läuft nicht mehr indirekt über `getattr(..., "data", None)`, sondern über einen eigenen sicheren Leser mit Fehlerabfangung.
- Das erste nutzbare Bild-HDU wird zusammen mit dem Header in einem Schritt ermittelt.

## Wirkung

- Mond-/Planet-FITS mit skalierten Integerdaten rendern wieder.
- Die Galerie-Thumbs für FITS-Dateien und die Detailvorschau teilen sich denselben stabileren Ladepfad.
