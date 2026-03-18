# Session-Detail kompakter sowie Solar-System-Zielname vereinheitlicht

## Ziel

Die Session-Detailseite soll auf Mobile weniger Höhe verschwenden.
Für Sonnen- und Mond-Sessions wird der Standort deshalb als einklappbares Modul dargestellt und nur offen gestartet, wenn noch kein direkter Session-Standort gesetzt ist.
Zusätzlich werden generische Zielnamen bei Sonnen- und Mond-Sessions als `Solarsystem` vereinheitlicht.

## Änderungen

### Session-Detail
- Reihenfolge im AstroManager-Bereich angepasst
- Mond-/Sonnenmodul vor Standortmodul
- Standortmodul als `details/summary`-Collapse umgesetzt
- Collapse standardmäßig offen bei Default-/Fallback-Standort oder fehlendem Standort
- Collapse standardmäßig geschlossen bei fest zugewiesenem Session-Standort
- Standortmodul nur noch für `sun`- und `moon`-Sessions

### Zielnamen
- generische Namen wie `Sun`, `Moon`, `Sonne`, `Mond` oder `Systemziel` werden bei `sun`/`moon` nicht mehr als eigentliches Target dargestellt
- wenn keine echte spezifische Zielbezeichnung existiert, wird `Solarsystem` verwendet
- gilt für Galerie und Session-Detail
