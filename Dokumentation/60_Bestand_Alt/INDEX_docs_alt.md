# AstroManager Dokumentationsindex

## Überblick

Diese Datei dient als Einstieg in die Projektdokumentation von AstroManager.

Die Dokumentation ist in mehrere thematische Dateien aufgeteilt, damit Architektur, Datenmodell, Pipeline, Resolver, UI und Roadmap sauber getrennt gepflegt werden können.

---

## Dokumente

### README.md
Einstieg und Gesamtüberblick über AstroManager.

Inhalt:
- Zweck
- Zielbild
- aktueller Stand
- Final-Merge
- UI-Stand
- Beispiele
- Prioritäten
- Verweise auf weitere Dokumente

### ARCHITECTURE.md
Beschreibt die Systemarchitektur und die Trennung zwischen Rohdaten, Resolvern, Merge, Pipeline und UI.

Inhalt:
- Hauptmodule
- Datenfluss
- Architekturprinzipien
- Zielklassen
- Systemgrenzen

### ROADMAP.md
Beschreibt den geplanten Ausbau von AstroManager.

Inhalt:
- bereits umgesetzt
- Feature-Priorisierung
- Pflicht / Bald / Später
- empfohlene Entwicklungsreihenfolge
- strategische Themen

### DATA_MODEL.md
Beschreibt die Struktur der Datenhaltung.

Inhalt:
- Tabelle `targets`
- Resolver-Felder
- finale Felder
- Qualitäts- und Trace-Felder
- spätere Tabellen und Objektarten

### RESOLVERS.md
Dokumentiert die aktuell eingebundenen externen Quellen und ihre Rollen.

Inhalt:
- Sesame
- Wikidata
- NED
- SIMBAD
- NASA Image Library
- Stärken und Grenzen jeder Quelle

### PIPELINE.md
Dokumentiert den Ablauf der Verarbeitung von Rohdaten bis zu finalen Zielen und späteren Stacks.

Inhalt:
- Rohdaten-Sync
- Indexierung
- Resolver-Anreicherung
- Final-Merge
- Kalibration
- Session-Stacks
- Gruppen-Stacks
- Mosaike
- Finalisierung

### STACKING_STRATEGY.md
Beschreibt die geplante Stacking-Logik.

Inhalt:
- Session-Stacks
- Gruppen-Stacks
- Mosaik-Stacks
- Final-Stacks
- Mehrtages-Logik
- Master-Dark-Pool

### UI_CONCEPT.md
Beschreibt Zielbild und Logik der Web-UI.

Inhalt:
- Tabs
- Targets-Tab
- Deep-Sky-Targets
- Systemziele
- spätere Detailansichten
- Such- und Filterlogik

### SOURCE_PRIORITY.md
Dokumentiert die Priorität der Quellen je Feld.

Inhalt:
- Name
- Koordinaten
- Anzeige-Typ
- Roh-Typ
- Distanz
- Bilder
- Systemziele

### KNOWN_ISSUES.md
Sammelt bekannte fachliche und technische Themen.

Inhalt:
- offene Probleme
- bewusste Vereinfachungen
- noch unvollständige Bereiche

### CHANGELOG.md
Kurzprotokoll der wichtigsten Entwicklungsschritte.

Inhalt:
- wesentliche erreichte Meilensteine
- größere Strukturänderungen
- wichtige Erweiterungen

---

## Empfohlene Lesereihenfolge

Für einen schnellen Einstieg:
1. `README.md`
2. `ROADMAP.md`
3. `ARCHITECTURE.md`

Für technische Arbeit am System:
1. `DATA_MODEL.md`
2. `RESOLVERS.md`
3. `PIPELINE.md`
4. `STACKING_STRATEGY.md`
5. `SOURCE_PRIORITY.md`

Für UI-Arbeit:
1. `UI_CONCEPT.md`
2. `README.md`
3. `ROADMAP.md`

---

## Pflegehinweise

- `README.md` soll kompakt und gut lesbar bleiben
- `ROADMAP.md` beschreibt Planung, nicht technische Details
- `DATA_MODEL.md` und `RESOLVERS.md` sollen fachlich präzise bleiben
- `PIPELINE.md` und `STACKING_STRATEGY.md` beschreiben Logik und Ablauf
- `KNOWN_ISSUES.md` wird bewusst offen und ehrlich gepflegt
- `CHANGELOG.md` dokumentiert wesentliche Fortschritte, nicht jede Kleinigkeit
