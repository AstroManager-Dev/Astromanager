# Wetter-Forecast: Standortnamen und Mobile-Layout

## Ziel
Der Wetterbereich soll gespeicherte Beobachtungsstandorte nicht nur technisch über Koordinaten anzeigen, sondern lesbar als Standort + Stadt/Stadtteil. Gleichzeitig wird die Mobile-Aufteilung verdichtet.

## Umsetzung
- Reverse-Geocoding pro Standort auf Basis der gespeicherten Koordinaten
- gecachte Standort-Meta unter `/cache/web/weather/`
- Anzeige im Wetterkopf:
  - Standortname
  - Stadt / Stadtteil
  - technische Detailzeile (Koordinaten, Höhe, Zeitzone)
- kompakter Standortwechsel über Select im Standortblock
- Wetterseite mobil neu strukturiert:
  - Aktuell als 2x2-Metrikgrid
  - hervorgehobene Karte für die nächste Nacht
  - weitere Nächte untereinander statt gequetschtem Mehrspaltengrid
  - Stundenverlauf als horizontale Kartenleiste statt breiter Tabelle
  - Tagesübersicht als kompaktes 2-Spalten-Grid

## Hinweise
- Reverse-Geocoding ist best-effort und fällt bei Fehlern auf die vorhandenen Standortdaten zurück.
- Standortname des Users bleibt maßgeblich; Stadt/Stadtteil wird nur ergänzend angezeigt.
