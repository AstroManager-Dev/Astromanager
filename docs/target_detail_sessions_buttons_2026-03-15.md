# Target-Detailseite mit Session-Buttons und Dwarf-Preview

## Umsetzung
- Detailseite zeigt oben die gleiche Target-Card wie die Targets-Liste, aber ohne Action-Button.
- Listenbutton in der Targets-Liste auf `Sessions ansehen` umbenannt.
- Session-Liste auf Button-Ansicht umgestellt und in eigene Include-Templates zerlegt.
- Unter jedem Session-Button werden EXP, Gain und Gesamtbelichtungsdauer gezeigt.
- Wenn vorhanden, wird das Dwarf-Stack-Previewbild der Session angezeigt.

## Berechnung
- Gesamtbelichtungsdauer = Anzahl Light-Files pro Session × `sessions.exp`
- Falls keine Light-Files zählbar sind, wird auf `sessions.frame_count` zurückgefallen.
