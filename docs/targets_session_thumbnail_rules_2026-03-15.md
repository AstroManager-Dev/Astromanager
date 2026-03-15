# Targets: Session-Thumbnail statt NASA-Bild

Stand: 2026-03-15

## Ziel
Auf der Target-Liste und der Target-Detailseite soll bevorzugt das `stacked_thumbnail.jpg` der neuesten passenden Session genutzt werden.

## Regeln
- Vorrang fuer Session-Thumbnail vor NASA-Bild
- nur `stacked_thumbnail.jpg`
- Quelle aus `raw_files` ueber `session_key`
- Deep-Sky nur bei plausibler Zielzuordnung
- Sun und Moon ohne Koordinatenpruefung

## Matching Deep-Sky
Ein Session-Thumbnail darf fuer ein Target genutzt werden, wenn mindestens eine der folgenden Bedingungen erfuellt ist:
- `session_targets.is_primary = 1`
- `session_targets.is_requested_target = 1`
- direkte Session-Zuordnung ueber `sessions.target_id`
- `session_targets.distance_to_center_deg <= 0.25`
- Fallback: Winkelabstand zwischen Target-Koordinaten und Session-Target-Koordinaten <= 0.25 Grad

## Zweck der Begrenzung
Begleitobjekte im selben Bildfeld sollen nicht das Kartenbild anderer Targets uebernehmen. Beispiel: Bei M31 koennen M32 und M110 im Feld liegen, bekommen dadurch aber nicht automatisch dasselbe Thumbnail.

## Web
- neue Medienroute fuer Bildauslieferung aus `raw_files.abs_path`
- erlaubte Roots: `/raw`, `/data`, `/runtime`
