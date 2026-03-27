# Wetter-Forecast auf Basis gespeicherter Standorte

## Ziel
Neue Wetter-Seite im Hauptbereich, die vorhandene `observing_sites` direkt verwendet.

## Umsetzung
- neue Fachlogik in `code/web/functions/weather.py`
- Forecast pro ausgewähltem Standort über Open-Meteo
- Standard-Standort wird bevorzugt, alternativ erster gespeicherter Standort
- aktuelle Wetterlage
- nächste 12 Stunden
- Nachtqualitätsübersicht für die nächsten Nächte
- 7-Tage-Vorschau
- Dateicache unter `/cache/web/weather/`

## Architektur
- keine DB-Erweiterung
- keine neue API-Key-Pflicht
- Forecast-Seite bleibt read-only
- Standortpflege bleibt in Einstellungen → Standorte

## Hinweis
Die Wetterdaten werden serverseitig vom Web-Container geladen und für kurze Zeit lokal gecacht.
