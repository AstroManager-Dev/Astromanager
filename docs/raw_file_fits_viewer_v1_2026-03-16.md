# RAW File FITS Viewer v1

Stand: Backup `0.4.018`

Umgesetzt:
- serverseitige FITS-PNG-Vorschau auf der RAW-Einzeldatei-Seite
- Umschalter `Datei | FITS`
- Debayer-Modi `Auto Debayer | Mono`
- FITS-Vorschaubilder für RAW-Listen als quadratische 1:1-Thumbs
- keine allgemeine Design-Überarbeitung, nur Viewer-Funktionalität

Technik:
- neues Fachmodul `code/web/functions/fits_viewer.py`
- Rendering mit `astropy`, `numpy`, `Pillow`
- Debayer v1 als einfacher Bayer-Demosaic-Pfad
- Vorschau-Endpunkt `/media/raw-file-fits-preview/<id>.png`

Offen:
- Cache für gerenderte FITS-Previews
- Histogramm / Stretch-Steuerung
- mehr Debayer-Modi
- Vergleich mit späteren AstroManager-Zwischenständen
