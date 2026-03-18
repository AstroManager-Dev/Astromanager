# Bottom Nav auf echtes Button-Set gezogen

## Problem
Die Bottom-Navigation nutzte weiter Altregeln aus `app.css` und sah trotz `astro-btn`-Klassen nicht wie das zentrale Button-Set aus. Zusätzlich war der Abstand zum Content zu klein, so dass Listen unten überdeckt wurden.

## Umsetzung
- `base.html` ergänzt um `bottom-nav__grid` und `bottom-nav__btn`
- `18_bottom_nav_cleanup.css` finalisiert
- Layout der Bottom-Bar getrennt vom Button-Stil
- sichtbarer Stil bleibt beim zentralen Button-System
- zusätzlicher Bodenabstand für Content, damit die Bottom-Bar nichts überdeckt

## Ergebnis
- alle fünf Bottom-Buttons nutzen denselben Stil
- `Menü` ist kein Sonderfall mehr
- `Zentrale`-Lock ist nur noch ein Icon innerhalb des gleichen Buttons
- Listen und Formulare laufen nicht mehr unter die Bottom-Bar
