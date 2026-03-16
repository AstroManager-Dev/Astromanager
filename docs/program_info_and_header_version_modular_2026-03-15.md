# Programm-Info und Header-Version modular ergänzt

## Umsetzung
- Header als Include `includes/_topbar_brand.html` modularisiert.
- Unter `DeepSky Sessions` wird `V. x.x.x` aus `VERSION` angezeigt.
- Programm-Info bleibt include-basiert:
  - `pages/program_info/_version_header.html`
  - `pages/program_info/_patch_log.html`
  - `pages/program_info/_minor_log.html`
- Daten kommen direkt aus:
  - `VERSION`
  - `SCHEMA_VERSION`
  - `CHANGELOG.unreleased.md`
  - `CHANGELOG.md`
