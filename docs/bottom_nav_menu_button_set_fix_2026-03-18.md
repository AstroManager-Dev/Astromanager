# Bottom-Nav Menü-Button auf Button-Set umgestellt

## Stand
Die Bottom-Navigation nutzte ab 0.4.033 bereits für Galerie, Atlas, Targets und Zentrale das neue Button-Set, der rechte Menü-Button blieb jedoch als Sonderfall im Altstil bestehen.

## Änderung
- Bottom-Navigation in `base.html` vollständig auf `astro-btn astro-btn--sm` vereinheitlicht
- aktiver Galerie-Button nutzt `astro-btn--primary`
- gesperrter Zentrale-Button bleibt gleicher Stil mit Schloss
- `18_bottom_nav_cleanup.css` regelt jetzt nur noch Grid, Breite und Abstände statt einen eigenen konkurrierenden Button-Look aufzubauen

## Ergebnis
Alle fünf Bottom-Buttons verwenden dasselbe Button-System und bleiben optisch in einer Reihe konsistent.
