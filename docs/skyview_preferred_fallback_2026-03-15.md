# SkyView vor NASA und dynamische SkyView-Frames

## Ziel
Target-Karten und Target-Detailseiten sollen nach Session-Thumbnails bevorzugt ein positionsbasiertes Referenzbild zeigen.

## Umsetzung
- Web-Fallback-Reihenfolge:
  1. passendes `stacked_thumbnail.jpg` aus Session
  2. `target_skyview_resolve.image_url`
  3. NASA-Thumbnail
- SkyView wird direkt aus der Resolver-Seitentabelle gelesen.
- `resolve_target_skyview.py` nutzt weiterhin nur Targets mit finalen Koordinaten.

## Dynamische Feldgröße
Die SkyView-Abfrage nutzt keine starre `Size=0.35` mehr.

Regeln:
- wenn `angular_size_arcmin` vorhanden ist:
  - Standardrahmen ungefähr `2.2 × Objektgröße`
  - Nebel etwas enger, aber mit Mindestfeld für sinnvolle Umgebung
- harte Klammerung auf `0.12° .. 3.0°`
- ohne Größenwert Fallback je Objekttyp:
  - Galaxie: `0.30°`
  - Sternhaufen: `0.35°`
  - Nebel: `0.80°`
  - sonst `0.35°`

## Survey-Wahl
- Standard: `DSS2 Color`
- für typische Emissions-/diffuse Nebel: `H-Alpha`

## Wirkung
- Deep-Sky-Karten zeigen jetzt bevorzugt koordinatenbasierte Referenzbilder statt textbasiertem NASA-Fallback.
- NASA bleibt nur noch Beauty-Fallback.
