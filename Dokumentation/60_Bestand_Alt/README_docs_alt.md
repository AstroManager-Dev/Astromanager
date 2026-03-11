# AstroManager

## Überblick

AstroManager ist ein lokales System zur Verwaltung, Anreicherung, Bewertung und Darstellung astronomischer Ziele, Sessions, Kalibrationsdaten, Stacks und Medienquellen.

Der Fokus liegt aktuell auf:
- Resolver- und Metadatenlogik
- Pipeline- und Stacklogik
- Web-UI für Targets und Rohdaten

## Zielbild

AstroManager soll:
- Ziele automatisch identifizieren und anreichern
- Rohdaten, Sessions und Stacks strukturiert verwalten
- Kalibrationsdaten zentral verwalten
- Session- und Stack-Beziehungen über mehrere Tage abbilden
- perspektivisch VLM-gestützte Bewertung und Postproduktion unterstützen

## Aktueller Stand

### Quellen und Resolver

#### Sesame
Für erste Zielauflösung und Basis-Koordinaten.

#### Wikidata
Für Labels, Aliasse, Wikipedia-Bezüge, Typ-Labels und Distanzfelder.

#### NED
Für astrophysikalische Basisdaten, bevorzugte Namen, Typen, Koordinaten und Redshift.

#### SIMBAD
Für astronomische Roh-Typen, Haupt-IDs und Koordinaten.

#### NASA Image Library
Für Zielbilder, Detailseiten und Asset-Manifeste.

## Final-Merge

Wichtige finale Felder:
- `final_name`
- `final_objtype`
- `final_ra_deg`
- `final_dec_deg`
- `final_distance_value`
- `final_distance_unit`
- `final_source_summary`

Aktuelle Merge-Logik:
- Name: bevorzugt Wikidata
- Koordinaten: SIMBAD, dann NED, dann Sesame
- Anzeige-Typ: Wikidata, dann NED, dann SIMBAD
- Distanzanzeige: normiert in Lichtjahre

## Qualitäts- und Trace-Felder

- `distance_source`
- `distance_ref`
- `distance_ly`
- `identity_method`
- `identity_confidence`
- `coord_match_sep_arcsec`
- `constellation`

## UI-Stand

Die Web-UI besitzt:
- `Übersicht`
- `Targets`
- `DB`

Im `Targets`-Tab:
- Deep-Sky-Targets
- Systemziele
- NASA-Bild
- finaler Name
- Typ
- Sternbild
- RA/DEC
- Distanz
- Status

## Beispielziele

### M 31
- Name: Andromedagalaxie
- Typ: Spiralgalaxie
- Koordinaten: aus SIMBAD
- Distanz: in Lichtjahren normalisiert
- NASA-Bild: direktes Andromeda-Bild

### NGC 1499
- Name: Californianebel
- Typ: H-II-Gebiet
- Koordinaten: aus SIMBAD
- Distanz: in Lichtjahren
- NASA-Bild: California-Nebula-Bezug passend

## Zentrale Entscheidungen

- Sun und Moon werden als feste Systemziele behandelt
- Rohdaten und finale Darstellungsdaten bleiben getrennt
- Resolver werden quellenbasiert kombiniert
- Distanzanzeige erfolgt konsistent in Lichtjahren
- NASA-Medien werden mit Detailseite und Manifest gespeichert


## Prioritäten

Die aktuelle Feature-Priorisierung ist in `ROADMAP.md` dokumentiert.

Kurz zusammengefasst:
- **Pflicht:** Session-Gruppierung, Master-Dark-Pool, Stack-Hierarchie, Target-Matching, Target-Detailseite
- **Bald:** Qualitätsbewertung, Mosaik-Logik, Zielstatistiken, UI-Filter, bessere Medienlogik
- **Später:** VLM-Bildbewertung, VLM-Postproduktion, Planung, Export und Vergleichsansichten

## Verwandte Dokumente

Die zentrale Dokumentenübersicht liegt in:
- `INDEX.md`

Weitere Dokumente:
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `DATA_MODEL.md`
- `RESOLVERS.md`
- `PIPELINE.md`
- `STACKING_STRATEGY.md`
- `UI_CONCEPT.md`
- `SOURCE_PRIORITY.md`
- `KNOWN_ISSUES.md`
- `CHANGELOG.md`
