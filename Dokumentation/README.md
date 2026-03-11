# AstroManager – Dokumentation

## Zweck

Dieser Ordner ist der zentrale Einstiegspunkt für alle lesbaren Architektur-, Datenmodell-, Workflow- und Planungsdokumente des Projekts.

Ziel:
- klare Trennung zwischen Code und Dokumentation
- zentrale Ablage statt verteilter Einzeldateien
- bessere Wiederauffindbarkeit von Entscheidungen, Zielbildern und Umbauplänen

## Struktur

### 00_Leitlinien
Dauerhafte Grundregeln, Modellentscheidungen und Leitplanken.

### 10_Architektur
Gesamtarchitektur, Datenfluss, Systemaufbau, Zielbild.

### 20_Datenmodell
Tabellen, Beziehungen, Zielschema, Erweiterungsüberlegungen.

### 30_Workflows
Dokumente zu raw, index, calibration, siril, Session- und Group-Verarbeitung.

### 40_UI_und_API
Web-UI, feste Actions, Formulare, API- und Steuerungslogik.

### 50_Planung
Roadmaps, Umbaupläne, offene Architektur- und Schemaüberlegungen.

### 60_Bestand_Alt
Historische oder referenzierte Alt-Dokumente, die bewusst aufgehoben werden.

## Ablage-Regeln

- Lesbare Konzept- und Entscheidungsdokumente gehören nach `Dokumentation/`
- Direkte Code-Artefakte bleiben unter `code/`
- Historische Bestände werden nicht vermischt, sondern unter `60_Bestand_Alt` gesammelt
- Neue Architektur- oder Schema-Überlegungen zuerst unter `50_Planung` ablegen
- Wenn eine Planung verbindlich wird, in den passenden Zielbereich verschieben

