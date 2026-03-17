# Target-Detail kompakter Header 2026-03-17

## Ziel
Auf der Target-Detailseite soll das Vorschaubild links und der Metablock rechts stehen, damit auf Mobile keine unnötige Höhe verloren geht.

## Umsetzung
- Header-Template auf klare Zweispaltenstruktur umgestellt
- eigenes Summary-Row-Markup statt indirekter Grid-Vererbung
- Vorschaubild fest links, Faktenblock fest rechts
- mobile Größen für 92/104 px abgestimmt

## Betroffene Dateien
- `code/web/templates/pages/target_detail/_target_header_card.html`
- `code/web/static/css/app.css`
