# AstroManager – Versionierung

Stand: 2026-03-08  
Status: verbindlich

## Zweck

Diese Datei definiert die verbindlichen Regeln für die Versionierung von AstroManager.

Ziel:
- klare Unterscheidung zwischen offiziellem Release und Zwischenständen
- nachvollziehbare Entwicklung von Code, Dokumentation und Datenmodell
- saubere Zuordnung von Backups zu einem Projektstand
- Trennung zwischen Projektversion und Schema-Version

---

## 1. Versionsarten

AstroManager verwendet zwei getrennte Versionslinien:

### 1.1 Projektversion
Die Projektversion beschreibt den fachlichen und funktionalen Gesamtstand des Projekts.

Beispiele:
- `0.1.000`
- `0.1.001`
- `0.1.002`
- `0.2.000`

### 1.2 Schema-Version
Die Schema-Version beschreibt ausschließlich den Stand des Datenbankschemas.

Beispiele:
- `1`
- `2`
- `3`

Wichtig:
- die Projektversion kann sich ändern, ohne dass sich das Schema ändert
- die Schema-Version kann sich ändern, ohne dass direkt ein großer Projektsprung nötig ist

---

## 2. Format der Projektversion

Format:

`MAJOR.MINOR.PATCH`

Für AstroManager wird dieses Format aktuell so verwendet:

- `0.1.000` = offizieller Basisstand einer Entwicklungsphase
- `0.1.001` = kleine Änderung innerhalb derselben Phase
- `0.1.002` = weitere kleine Änderung innerhalb derselben Phase
- `0.2.000` = nächster definierter Meilenstein

### Bedeutung

#### MAJOR
Aktuell noch `0`, solange AstroManager sich im Aufbau und in aktiver Strukturentwicklung befindet.

#### MINOR
Steht für einen echten fachlichen Meilenstein oder neuen Projektabschnitt.

Beispiele:
- `0.1.000` = erster definierter Referenzstand
- `0.2.000` = nächster klarer Ausbauzustand

#### PATCH
Steht für kleinere Änderungen innerhalb derselben MINOR-Phase.

Beispiele:
- kleine Script-Anpassung
- kleine Doku-Erweiterung
- kleinere UI- oder Logikverbesserung
- kleinere Korrektur an Backup, Struktur oder Text

---

## 3. Aktueller offizieller Startpunkt

Der erste offizielle Referenzstand ist:

- **Projektversion:** `0.1.000`
- **Schema-Version:** `1`

Dieser Stand markiert den ersten sauber versionierten Projektzustand mit:
- zentraler Dokumentationsstruktur
- versioniertem Backup
- offizieller `VERSION`
- offizieller `SCHEMA_VERSION`
- getrenntem `CHANGELOG.md`
- getrenntem `CHANGELOG.unreleased.md`

---

## 4. Welche Datei wofür zuständig ist

### 4.1 `VERSION`
Pfad:
`/home/pi/docker/astromanager/VERSION`

Inhalt:
- genau eine Zeile mit der aktuellen offiziellen oder laufenden Projektversion

Beispiel:
`0.1.000`

### 4.2 `SCHEMA_VERSION`
Pfad:
`/home/pi/docker/astromanager/SCHEMA_VERSION`

Inhalt:
- genau eine Zeile mit der aktuellen Schema-Version

Beispiel:
`1`

### 4.3 `CHANGELOG.md`
Pfad:
`/home/pi/docker/astromanager/CHANGELOG.md`

Zweck:
- enthält nur offizielle, freigegebene Release-Stände
- keine Kleinständerungen einzeln, solange sie noch nicht in einen offiziellen Meilenstein übernommen wurden

### 4.4 `CHANGELOG.unreleased.md`
Pfad:
`/home/pi/docker/astromanager/CHANGELOG.unreleased.md`

Zweck:
- sammelt laufende Änderungen seit dem letzten offiziellen Release
- dient als Zwischenpuffer bis zum nächsten offiziellen Versionssprung

---

## 5. Wann die PATCH-Version erhöht wird

Die PATCH-Version wird erhöht, wenn kleinere Änderungen umgesetzt werden, die keinen neuen fachlichen Meilenstein darstellen.

Beispiele:
- kleinere Anpassungen an Shell-Skripten
- kleinere Änderungen an Doku-Struktur
- kleinere Verbesserungen in der Web-UI
- kleine Korrekturen an Backups
- neue Leitliniendateien
- kleine Refactorings ohne neue große Fachfunktion

Beispiel:
- von `0.1.000` auf `0.1.001`
- von `0.1.001` auf `0.1.002`

Wichtig:
Diese Änderungen werden zunächst in `CHANGELOG.unreleased.md` gesammelt.

---

## 6. Wann auf einen neuen MINOR-Stand gesprungen wird

Ein Sprung auf `0.2.000`, `0.3.000` usw. erfolgt nur dann, wenn ein echter fachlicher Meilenstein erreicht ist.

Beispiele:
- neues Quellenmodell `device_sources` ist fachlich und technisch sauber eingeführt
- neue Kern-Tabellen wie `session_stacks` und `group_stacks` sind eingeführt
- ein neuer Workflow-Bereich ist operativ nutzbar
- eine größere Architekturänderung ist abgeschlossen
- ein neuer Projektabschnitt ist klar abgeschlossen und dokumentiert

Beispiel:
- `0.1.00x` wird zu `0.2.000`

---

## 7. Umgang mit `CHANGELOG.unreleased.md`

`CHANGELOG.unreleased.md` sammelt alle Änderungen seit dem letzten offiziellen Release.

Empfohlene Bereiche:
- `Added`
- `Changed`
- `Fixed`
- `Planned`

Diese Datei darf auch unvollständiger und arbeitsnäher sein als das offizielle Changelog.

---

## 8. Übergang von Unreleased zu offiziellem Release

Beim Sprung auf einen neuen offiziellen MINOR-Stand gilt:

### Schritt 1
Inhalt von `CHANGELOG.unreleased.md` prüfen und bereinigen

### Schritt 2
Relevante Punkte in das offizielle `CHANGELOG.md` als neuer Versionsblock übernehmen

### Schritt 3
`VERSION` auf den neuen offiziellen Stand setzen

Beispiel:
- von `0.1.007` auf `0.2.000`

### Schritt 4
`CHANGELOG.unreleased.md` zurücksetzen und neu beginnen

### Schritt 5
Falls nötig, `SCHEMA_VERSION` ebenfalls erhöhen

---

## 9. Wann die Schema-Version erhöht wird

Die Schema-Version wird erhöht, wenn sich das Datenbankschema ändert.

Beispiele:
- neue Tabelle
- neue Spalte
- neue Relation
- neue Indizes, wenn sie strukturell relevant sind
- neue Migration, die das Schema fachlich verändert

Nicht automatisch schema-relevant:
- reine Doku-Änderung
- reine Script-Änderung ohne DB-Auswirkung
- reine UI-Textänderung

Beispiel:
- `SCHEMA_VERSION` von `1` auf `2`

Wichtig:
Die Schema-Version ist unabhängig von der Projektversion zu betrachten.

---

## 10. Zusammenhang zwischen Projektversion und Backups

Backups sollen immer die aktuelle Projektversion im Dateinamen tragen.

Beispiel:
`astromanager_v0.1.000_2026-03-08_10-20-10.zip`

Vorteil:
- Backups sind sofort einem fachlichen Stand zuordenbar
- mehrere Backups derselben Phase bleiben trotzdem über Zeitstempel unterscheidbar

---

## 11. Zusammenhang zwischen Projektversion und Dokumentation

Wichtige Dokumente dürfen zusätzlich einen eigenen Kopf enthalten mit:
- Stand
- Status
- optional Dokumentversion

Beispiel:
- `Stand: 2026-03-08`
- `Status: verbindlich`

Das ersetzt nicht die Projektversion, sondern ergänzt sie.

---

## 12. Praktische Arbeitsregel

### Offizielle Dateien
- `VERSION`
- `SCHEMA_VERSION`
- `CHANGELOG.md`

Diese Dateien beschreiben den verbindlichen Stand.

### Laufende Arbeitsdatei
- `CHANGELOG.unreleased.md`

Diese Datei sammelt Zwischenstände und laufende Änderungen.

---

## 13. Aktuelle Regel für AstroManager

Ab sofort gilt:

- Startbasis ist `0.1.000`
- kleinere Änderungen erhöhen auf `0.1.001`, `0.1.002`, `0.1.003` usw.
- diese Änderungen werden zuerst in `CHANGELOG.unreleased.md` gesammelt
- beim Sprung auf `0.2.000` wird der bereinigte Inhalt in `CHANGELOG.md` übernommen
- `CHANGELOG.unreleased.md` wird danach neu gestartet
- Schema-Änderungen erhöhen zusätzlich `SCHEMA_VERSION`

---

## 14. Beispiel

### Ausgangslage
- `VERSION = 0.1.000`
- `SCHEMA_VERSION = 1`

### Kleine Änderung
- Backup-Skript verbessert
- Doku-Struktur erweitert

Ergebnis:
- `VERSION = 0.1.001`
- `SCHEMA_VERSION = 1`
- Eintrag in `CHANGELOG.unreleased.md`

### Größerer Ausbau
- `device_sources` fachlich und technisch sauber eingeführt
- neue Stack-Tabellen ergänzt

Ergebnis:
- `VERSION = 0.2.000`
- `SCHEMA_VERSION` steigt ggf. auf `2`
- Übernahme der relevanten unreleased Punkte in `CHANGELOG.md`

---

## 15. Kernaussage

AstroManager unterscheidet ab jetzt sauber zwischen:

- offiziellem Release-Stand
- laufenden Zwischenänderungen
- Datenbankschema-Stand

Damit bleiben Projektentwicklung, Dokumentation, Migrationen und Backups konsistent nachvollziehbar.

