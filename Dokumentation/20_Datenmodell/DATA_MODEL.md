# AstroManager Datenmodell

## Grundprinzip

Das Datenmodell trennt zwischen:
- Rohquellenfeldern
- quellenbezogenen Resolverfeldern
- finalen Merge-Feldern
- Qualitäts- und Trace-Feldern

## Tabelle `targets`

### Identität und Grundstruktur
- `id`
- `canonical_name`
- `display_name`
- `category`
- `created_at`
- `updated_at`

### Sesame / Grundkoordinaten
- `ra_deg`
- `dec_deg`
- `coord_text`
- `coord_source`
- `coord_ref`
- `coord_status`

### Wikidata
- `wikidata_id`
- `label_de`
- `label_en`
- `aliases_de`
- `aliases_en`
- `wiki_de_title`
- `wiki_en_title`
- `object_type`
- `object_type_label_de`
- `object_type_label_en`
- `mag_value`
- `mag_band`
- `distance_value`
- `distance_unit`
- `distance_unit_label_de`
- `distance_unit_label_en`
- `name_status`
- `name_source`
- `name_resolved_at`
- `meta_status`
- `meta_source`
- `meta_resolved_at`

### NED
- `ned_preferred_name`
- `ned_objtype`
- `ned_ra_deg`
- `ned_dec_deg`
- `ned_redshift`
- `ned_status`
- `ned_source`
- `ned_resolved_at`

### SIMBAD
- `simbad_main_id`
- `simbad_otype`
- `simbad_ra_deg`
- `simbad_dec_deg`
- `simbad_status`
- `simbad_source`
- `simbad_resolved_at`

### NASA
- `nasa_title`
- `nasa_nasa_id`
- `nasa_page_url`
- `nasa_asset_manifest_url`
- `nasa_thumb_url`
- `nasa_image_url`
- `nasa_status`
- `nasa_source`
- `nasa_resolved_at`

### Finale Felder
- `final_name`
- `final_objtype`
- `final_ra_deg`
- `final_dec_deg`
- `final_distance_value`
- `final_distance_unit`
- `final_source_summary`

### Qualität und Nachvollziehbarkeit
- `distance_source`
- `distance_ref`
- `distance_ly`
- `identity_method`
- `identity_confidence`
- `coord_match_sep_arcsec`
- `constellation`

## Künftige Tabellen / Objekte

### Sessions
Für einzelne Beobachtungssitzungen.

### Raw Files
Für Einzeldateien und Headerdaten.

### Calibration Assets
Für Dark-, Flat- und weitere Kalibrationspools.

### Session Stacks
Für pro Session erzeugte Stacks.

### Group Stacks
Für gruppierte Mehrtages-Stacks.

### Mosaic Stacks
Für zusammengesetzte Mosaik-Verarbeitung.

### Final Products
Für finale Bilder, Vorschauen und veröffentlichte Ergebnisse.
