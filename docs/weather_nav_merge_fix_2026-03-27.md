# Wetter/Navigation Merge-Fix 2026-03-27

## Zweck
Konsolidierter Reparaturstand nach Rückfall auf ältere Navigations-Templates.

## Enthalten
- Bottom-Navigation wieder als kompakte Icon-Navigation
- Wetter und Planner wieder in Bottom-Navigation und Menü vorhanden
- Wetterseite als Haupt-Tab eingebunden
- Planner als Haupt-Tab eingebunden
- Wetter-Standortkopf ohne ungeeignete Freitext-Zeitzone in der Detailzeile
- Standort-Zeitzone nur noch bei gültigem IANA-Wert separat anzeigen
- Statuszeit auf lokaler Standortzeit statt UTC-Label umgestellt
- Nächste 12 Stunden ab aktueller Forecast-Stunde statt ab Tagesanfang
- Nachtkarten filtern vergangene Nachtfenster abhängig von der aktuellen lokalen Stunde aus

## Hinweise
- Reverse-Geocoding ergänzt Stadt und Stadtteil ergänzend zum gespeicherten Standortnamen.
- Für Freitext wie `Berlin` wird bewusst nicht mehr so getan, als sei dies eine technische Zeitzone.
- Planner bleibt im aktuellen Stand ein vorbereiteter Platzhalterbereich.
