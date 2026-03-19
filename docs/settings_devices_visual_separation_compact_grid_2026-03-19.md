# Settings Devices UI – kompakter Grid-Aufbau und klarere Trennung

## Ziel
Der Gerätebereich sollte deutlich kompakter und besser gegliedert werden:
- vorhandene Instanzen zuerst
- neue Instanz danach
- Sources ganz unten
- optisch klarer getrennte Module
- weniger Scrollhöhe
- Bearbeitung nur bei Bedarf sichtbar

## Umsetzung
- Reihenfolge der Module in `_devices.html` angepasst
- Geräteinstanzen als kompakte 2-Spalten-Karten umgesetzt
- Source-Templates ebenfalls als kompakte 2-Spalten-Karten umgesetzt
- neue Instanz bleibt per Button-Toggle verborgen
- Bearbeitungsformular pro Instanz bleibt per Button-Toggle verborgen
- CSS für klarere Modultrennung, kompaktere Innenabstände und saubere Kartenlogik überarbeitet

## Ergebnis
Der Gerätebereich wirkt näher an einem Dashboard-/Widget-Aufbau:
- oben relevante Instanzen
- mittig nur bei Bedarf neue Anlage
- unten read-only Sources
