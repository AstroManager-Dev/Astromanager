# Target-Bildresolver erweitert

## Umgesetzt
- neuer eigener Resolver `resolve_target_legacy_survey.py`
- eigene Resolver-Tabelle `target_legacy_survey_resolve`
- eigene Steps `0825` und `0826`
- Bild-Fallback im Web jetzt: Session -> Legacy Survey -> SkyView -> NASA
- SkyView markiert Antworten mit `no data` oder unbrauchbare Antworten nicht mehr als `resolved`

## DB
- Erweiterung ueber Migration `code/db/migrations/0002_target_image_resolvers.sql`
- `db_init` fuehrt Migrations jetzt nach dem Baseline-Schema aus
- Baseline-Schema wurde ebenfalls auf den neuen Resolverstand gebracht

## Fachlogik ausgelagert
- `astromanager.targets.image_resolver_rules`
- `astromanager.targets.image_validation`

Darin zentralisiert:
- Survey-/Layer-Wahl
- FOV-/Frame-Regeln
- Blank-/No-Data-Validierung fuer SkyView
- gemeinsame Konstanten fuer Resolver
