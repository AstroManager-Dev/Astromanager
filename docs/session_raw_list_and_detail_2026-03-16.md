# Session RAW-Liste und Einzeldatei 2026-03-16

- Session-Seite bleibt session-zentriert.
- RAW-Dateien laufen über eigene Liste unter `/sessions/<id>/raw`.
- Liste paginiert mit 10/20/50/100 Einträgen.
- Klick aus der Liste führt auf eine Einzeldatei-Seite, nicht auf Vollbild.
- Einzeldatei-Seite bietet Bild/FITS-Dummy, Metadaten und Download.
- Download läuft über eigene Route `/download/raw-file/<id>`.
- Belichtung wird direkt in Sekunden wie `15s` angezeigt, nicht hochgerechnet auf Minuten.
