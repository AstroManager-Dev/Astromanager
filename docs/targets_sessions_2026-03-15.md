# Targets: Session-Zuordnung und Detailseite

## Stand
- Kartenanzahl für Targets zählt Sessions jetzt nicht nur aus `session_targets`, sondern zusätzlich direkt aus `sessions.target_id`.
- Dadurch werden Sun- und Moon-Sessions in der Targets-Ansicht korrekt angezeigt.
- Neue Detailseite `/targets/<id>` listet alle zum Target gehörenden Sessions absteigend nach Datum.

## Zuordnungslogik
- Primär: direkte Zuordnung über `sessions.target_id`
- Zusätzlich: Feld-/Resolver-Treffer über `session_targets.target_id`
- Für Zähler wird die Vereinigungsmenge genutzt, damit doppelte Session-Target-Treffer nicht doppelt gezählt werden.

## UI
- Target-Karten verlinken auf die neue Detailseite.
- Detailseite zeigt Basisdaten des Targets und gruppiert Sessions pro Datum.
