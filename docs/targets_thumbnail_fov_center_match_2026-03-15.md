# Targets: Session-Thumbnail per FOV-Mittelkreis

Stand: 2026-03-15

## Ziel

Target-Karten und Target-Details sollen nur dann ein `stacked_thumbnail.jpg` aus einer Session übernehmen,
wenn das Bild fachlich wirklich zum Target gehört.

## Regelwerk

### Sun / Moon

- keine Koordinatenprüfung
- neueste passende Session mit `stacked_thumbnail.jpg` wird verwendet
- NASA bleibt nur Fallback

### Deep Sky

Ein Session-Thumbnail wird nur übernommen, wenn mindestens eine dieser Bedingungen erfüllt ist:

1. `sessions.target_id = targets.id`
2. `session_targets.is_requested_target = 1`
3. `session_targets.is_primary = 1`
4. Fallback über Koordinaten-Mittelkreis:
   - exakte Session-FOV aus `sessions.solve_fov_x_deg` und `sessions.solve_fov_y_deg`
   - Mittelkreis-Radius = `min(fov_x_deg, fov_y_deg) * 0.05`
   - das entspricht maximal 10% Mittendurchmesser bezogen auf die kleinere FOV-Kante
   - Target muss innerhalb dieses Mittelkreises liegen

## Abstandsermittlung

Priorität:

1. `session_targets.distance_to_center_deg`
2. falls nicht vorhanden: sphärischer Abstand zwischen
   - Session-Zentrum `solve_ra_deg/solve_dec_deg`
   - Target-Zentrum `final_ra_deg/final_dec_deg`

## Auswahlreihenfolge

Bei mehreren gültigen Kandidaten gewinnt:

1. direkte Session-Zuordnung
2. requested target
3. primary target
4. Mittelkreis-Treffer
5. neueste Session

## Erwartetes Verhalten im aktuellen DB-Stand

- M31 bekommt das M31-Thumbnail
- M110, M32 und NGC 206 übernehmen das M31-Bild nicht mehr
- IC 2027 / IC 2005 übernehmen das California-Nebel-Bild nicht mehr nur wegen Randlage im Feld
- Sun und Moon nutzen weiter ihr aktuelles Session-Bild ohne Koordinatenfilter
