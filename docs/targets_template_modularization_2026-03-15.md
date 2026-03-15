# Targets-Template-Modularisierung

## Ziel
Die Targets-Seite wird für leichtere Bearbeitung in eigene Template-Bausteine zerlegt.

## Struktur
- `pages/_targets.html`
  - nur Einstieg und Includes
- `pages/targets/_deepsky_section.html`
  - Deep-Sky-Block
- `pages/targets/_solarsystem_section.html`
  - Solarsystem-Block
- `pages/targets/_target_card.html`
  - gemeinsame Kartenstruktur für beide Bereiche
- `pages/targets/_target_card_image.html`
  - Bildausgabe inklusive Bildquellen-/Fallback-Logik

## Wirkung
- keine doppelte Kartenstruktur in den beiden Bereichen
- Bildblock zentral an einer Stelle wartbar
- spätere Erweiterungen an Target-Karten deutlich einfacher
