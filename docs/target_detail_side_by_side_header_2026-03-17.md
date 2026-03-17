# Target-Detail Header nebeneinander

## Ziel
Die Target-Detailseite soll das Vorschaubild und die wichtigsten Metadaten nebeneinander zeigen, statt erst Bild und danach Meta untereinander zu stapeln.

## Umsetzung
- Header-Card in `pages/target_detail/_target_header_card.html` auf zweispaltiges Detail-Layout umgestellt
- linke Spalte: quadratische Preview
- rechte Spalte: Metafakten im kompakten Grid
- bestehende Faktenstruktur und Feldinhalte beibehalten

## Ergebnis
- weniger vertikaler Leerraum
- schnellere Erfassung auf Mobile
- konsistenterer Nutzwert direkt im ersten Card-Block
