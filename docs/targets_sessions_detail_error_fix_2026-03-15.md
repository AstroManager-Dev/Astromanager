# Targets-Detailseite Fehlerfix 2026-03-15

## Problem
Die neue Target-Detailseite konnte in Live-Umgebungen mit 500 abbrechen, wenn die Session-Abfrage Annahmen über Tabellen oder Spalten traf, die im laufenden Stand nicht robust genug abgesichert waren.

## Lösung
- Session-Abfrage für Target-Details auf Tabellen- und Spaltenexistenz gehärtet
- Detailseite auf eigenes schlankes Wrapper-Template umgestellt
- Session-Felder mit Fallback-NULLs abgesichert
- Detailseite liefert auch dann stabil, wenn nur direkte `sessions.target_id`-Zuordnungen vorhanden sind

## Verhalten
- Sessions pro Target weiterhin aus direkter Session-Zuordnung und `session_targets`
- Ausgabe gruppiert nach Datum
- direkte vs. Resolver/Feld-Zuordnung sichtbar
