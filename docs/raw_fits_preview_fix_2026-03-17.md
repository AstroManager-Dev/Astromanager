# RAW-Liste und FITS-Preview Fix 2026-03-17

## Änderungen
- Light-Erkennung in `gallery.py` an `derivative_kind` erweitert, damit Session-Zähler und RAW-Liste dieselbe Logik verwenden.
- FITS-Thumbnails in der RAW-Liste priorisiert, damit bei FITS nicht auf allgemeine Fallback-Pfade zurückgefallen wird.
- RAW-Listenlayout beruhigt: größeres quadratisches Thumbnail, sauberer Textblock, Pfad schwächer und auf zwei Zeilen begrenzt.
- RAW-Datei-Viewer nutzt die aktive FITS-Vorschau ohne Layout-Umbau.

## Zweck
- `Lights 0` bei gleichzeitig gefüllter RAW-Liste vermeiden.
- FITS-Preview in Liste und Detail konsistent sichtbar machen.
- RAW-Liste lesbar halten, ohne das bestehende Designsystem umzubauen.
