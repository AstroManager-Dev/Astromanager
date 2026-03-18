# Beobachtungsstandorte sowie Sonnen-/Mondinfos pro Session

## Ziel

Standorte werden als eigene Stammdaten gepflegt und optional direkt an Sessions gebunden.
Auf dieser Basis werden für `sun`- und `moon`-Sessions zusätzliche Ephemeris-Daten in eigenen Seitentabellen gespeichert und auf der Session-Detailseite angezeigt.

## Datenmodell

### Neue Tabellen
- `observing_sites`
- `session_moon_ephemeris`
- `session_sun_ephemeris`

### Sessions
- `sessions.observing_site_id`

## UI

### Einstellungen
Neue Sektion **Standorte** unter `/settings?section=locations`.

Module:
- gespeicherte Standorte
- neuer Standort
- aktueller Browser-/Handy-Standort als Formularhilfe

### Session-Detailseite
Im AstroManager-Bereich:
- Standortmodul mit Session-Zuordnung
- Mondinfos für `category = moon`
- Sonneninfos für `category = sun`

## Berechnung

Aktuell über `swisseph`.

### Mit Standort
- Höhe
- Azimut
- Rise/Set/Transit
- bei Sonne zusätzlich Airmass

### Ohne Standort
- geozentrische Fallback-Werte
- Session bleibt dennoch auswertbar

## Hinweis

Mehrere Standorte sind anlegbar.
Löschung ist blockiert, solange Sessions direkt auf den Standort zeigen.
