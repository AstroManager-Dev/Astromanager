# AstroManager Architektur

## Ziel

AstroManager trennt bewusst zwischen:
- Rohdaten
- quellenbezogener Anreicherung
- fachlichem Merge
- Pipeline-Verarbeitung
- UI-Darstellung

## Hauptmodule

### Datenhaltung
SQLite-Datenbank für:
- Targets
- Sessions
- Rohdateien
- Kalibrationsdaten
- spätere Stack-Objekte
- spätere Mosaik- und Gruppenstrukturen

### Resolver-Schicht
Getrennte Resolver für:
- Sesame
- Wikidata
- NED
- SIMBAD
- NASA Image Library

### Merge-Schicht
Führt Rohfelder in finale Zielfelder zusammen:
- finale Anzeige-Namen
- finale Typen
- finale Koordinaten
- finale Distanzdarstellung
- Quellenzusammenfassung

### Pipeline-Schicht
Verarbeitet:
- Rohsessions
- Kalibrationsdaten
- Session-Zuordnung
- spätere Stacks und Stack-Gruppen
- spätere Mosaike
- spätere Finalprodukte

### UI-Schicht
Stellt Daten logisch dar:
- Übersicht
- Targets
- DB
- spätere Detailansichten

## Architekturprinzipien

### Trennung von Roh- und Finaldaten
Quellfelder bleiben erhalten, Finalfelder werden separat berechnet.

### Quellenrollen statt Einheitsresolver
Jede Quelle hat eine definierte Aufgabe.

### Nachvollziehbarkeit vor Abkürzung
Herkunft, Auswahl und Sicherheit eines Feldes sollen später nachvollziehbar bleiben.

## Datenfluss

### 1. Rohaufnahme
Sessions und Rohdaten werden indexiert.

### 2. Zielauflösung
Bekannte Zielnamen oder Header-Infos werden gegen Targets aufgelöst.

### 3. Quellenanreicherung
Resolver schreiben quellenbezogene Felder.

### 4. Merge
Finale Zielfelder werden priorisiert zusammengesetzt.

### 5. UI und weitere Verarbeitung
Finale Zielansicht, spätere Stack-Logik, Qualitätslogik und Postproduktionslogik.

## Zielklassen

Aktuell sinnvoll getrennt:
- `deepsky`
- `sun`
- `moon`

Später denkbar:
- `planet`
- `star`
- `cluster`
- `nebula`
- `galaxy`
- `mosaic`
- `solar_system`

## Besondere Entscheidungen

### Systemziele separat
Sun und Moon werden nicht wie normale Deep-Sky-Ziele behandelt.

### Medien getrennt von Fachwerten
NASA-Bilder ergänzen ein Target, definieren es aber nicht.

### Distanz normiert
Finale Distanzdarstellung erfolgt bevorzugt in Lichtjahren.

## Perspektive

Die Architektur ist vorbereitet auf:
- Session-Gruppierung
- Stack-Objekte
- Gruppen-Stacks
- Mosaik-Stacks
- versionierte Finalprodukte
- VLM-Bildbewertung
- VLM-Postproduktionsvorschläge
