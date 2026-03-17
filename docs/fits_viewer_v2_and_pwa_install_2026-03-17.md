# FITS-Viewer v2 und PWA-Installbutton 2026-03-17

## Änderungen
- FITS-Viewer auf der RAW-Datei-Detailseite zu einer nicht-destruktiven Vorschau ausgebaut.
- Viewer-Regler ergänzt:
  - Debayer: Auto / Mono
  - Stretch: Auto Stretch / Linear / Arcsinh
  - Black %
  - White %
  - Gamma
- Presets ergänzt:
  - Auto
  - Linear
  - Nebula
- FITS-Preview-Route gehärtet:
  - Platzhalter-PNG statt leerer/kaputter Antwort bei Fehlern
  - Cache für gerenderte Varianten unter `/cache/web/fits_viewer`
- RAW-Listen-Thumbs mit Browser-Fallback versehen, damit defekte Bildantworten nicht als kaputte Icons stehenbleiben.

## PWA
- `manifest.webmanifest` ergänzt
- Service Worker `sw.js` ergänzt
- Installationsbutton im Menü ergänzt
- `beforeinstallprompt` in `app.js` abgefangen und mit eigenem Button verbunden
- App-Icons unter `code/web/static/pwa/` ergänzt

## Zweck
- FITS-Vorschau produktiv benutzbar machen
- kleine Viewer-Bearbeitung direkt im Browser erlauben, ohne Quelldateien zu ändern
- AstroManager installierbar als Web-App auf Android machen
