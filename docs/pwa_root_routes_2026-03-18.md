# PWA Root-Auslieferung für Manifest und Service Worker

## Problem

Im echten Stand lagen `manifest.webmanifest` und `sw.js` nur unter `code/web/static/`,
während das Layout und die Service-Worker-Registrierung Root-URLs erwarteten:

- `/manifest.webmanifest`
- `/sw.js`

Dadurch war die PWA-Verdrahtung inkonsistent. Besonders der Service Worker unter
`/static/sw.js` hätte die eigentliche App unter `/` und `/#gallery` nicht mit dem
gewünschten Scope kontrolliert.

## Lösung

In `code/web/app.py` werden zwei Root-Routen ergänzt:

- `GET /manifest.webmanifest`
- `GET /sw.js`

Beide liefern die vorhandenen Dateien aus `code/web/static/` aus.
Zusätzlich sendet die `sw.js`-Route den Header `Service-Worker-Allowed: /`, damit
der Worker die komplette App unter Root kontrollieren darf.

## Ergebnis

Die bestehenden Referenzen bleiben korrekt:

- `<link rel="manifest" href="/manifest.webmanifest">`
- `navigator.serviceWorker.register("/sw.js")`

Damit ist die PWA-Auslieferung mit dem tatsächlichen App-Scope konsistent.
