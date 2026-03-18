# RAW-Liste, FITS-Viewer und zentrales Button-System

## Stand
- FITS-Dateien in der RAW-Liste öffnen jetzt direkt den FITS-Viewer.
- `Details` bleibt separate Datei-Seite.
- FITS-Dateien auf der Datei-Seite öffnen ohne `view`-Parameter direkt im FITS-Viewer.

## UI
- Zentrales Button-System im Stil der Aktionskarten ergänzt.
- Kleine Buttons, Tabs, Viewer-Chips und Page-Size-Buttons verwenden denselben Stil.
- RAW-Karten haben jetzt zwei klare Aktionen: `Viewer öffnen` und `Details`.

## FITS-Viewer
- OpenCV wird als bevorzugter Debayer-Pfad verwendet.
- Manuelle Bayer-Muster: `RGGB`, `BGGR`, `GRBG`, `GBRG`, `Mono`.
- Nach Debayering werden Background-Neutralisierung und Green-Reduction angewendet.

## Hinweise
- Ohne OpenCV fällt der Renderer weiter auf den Python-Fallback zurück.
- Die RAW-Liste rendert weiterhin absichtlich keine FITS-Thumbnails, um Mobil-Performance zu schonen.
