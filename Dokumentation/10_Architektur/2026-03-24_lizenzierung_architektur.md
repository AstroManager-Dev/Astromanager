# AstroManager – Lizenzierungsarchitektur vorbereiten
Stand: 2026-03-24

## Ziel

AstroManager soll als **eine App mit mehreren Editionsstufen** betrieben werden.

Geplante Außenstufen:
- Free
- Basic
- Plus
- Pro

Wichtig:
- keine getrennten App-Versionen
- keine getrennten Docker-Images pro Edition
- keine verteilten Hardcodes wie `if pro` über die ganze Codebasis

Stattdessen gilt intern:

**Editionen außen, Feature-Flags innen.**

---

## Architekturprinzip

Die technische Kette soll später so aussehen:

1. Lizenzquelle bestimmen
2. Edition auflösen
3. Feature-Menge ableiten
4. zentrale Guards bereitstellen
5. UI, API, Jobs und Commands greifen nur noch auf diese Guards zu

Für den vorbereitenden Stand wurde noch **keine kryptografische Lizenzdatei** eingeführt.
Stattdessen gibt es bewusst nur eine **Runtime-Edition über Umgebungsvariable**, damit die Modultrennung schon jetzt sauber vorbereitet werden kann.

---

## Aktueller vorbereitender Stand

Neue zentrale Lizenzierungsbausteine:
- `astromanager.licensing.feature_registry`
- `astromanager.licensing.edition_matrix`
- `astromanager.licensing.runtime`
- `code/web/functions/licensing.py`

Diese Schicht liefert bereits:
- zentrale Feature-Codes
- zentrale Editionsmatrix
- Runtime-Edition aus `ASTROMANAGER_LICENSE_EDITION`
- zentrale Helper wie `runtime_has_feature()` und `require_runtime_feature()`
- globalen Template-Kontext für spätere UI-Guards

---

## Warum die Vorbereitung jetzt wichtig ist

Spätere Lizenzierung wird nur dann wartbar, wenn die fachlichen Module bereits sauber geschnitten sind.

Nicht sinnvoll wäre:
- Editionen direkt in Fachmodulen zu vermischen
- Menü, API und Jobs mit unterschiedlichen Einzelregeln zu pflegen
- dieselbe Funktion mehrfach unterschiedlich zu sperren

Die neue Vorbereitung soll genau das verhindern.

---

## Geplante spätere Ausbaustufe

Nach dieser Vorbereitungsphase kann darauf sauber aufgebaut werden:

### Phase 1
- Runtime-Edition per Env bleibt als Dev-/Test-Mechanismus
- neue Module werden bereits einer Edition zugeordnet
- erste Guards an UI, API und Jobs

### Phase 2
- lokale signierte Lizenzdatei
- Installations-ID
- Lizenzstatusseite in der Web-UI
- Reload/Upload der Lizenz

### Phase 3
- optionale Online-Aktivierung
- Reissue-/Transfer-Prozess
- Update-Berechtigung getrennt von Nutzungsberechtigung

---

## Guard-Regel

Lizenzierung darf später nicht nur im Frontend stattfinden.

Pflichtbereiche für spätere Guards:
- Web-UI-Aktionen
- API-Endpunkte
- Worker-/Runner-Jobs
- Commands mit produktiver Wirkung
- teure oder editionsgebundene Verarbeitungsschritte

Frontend allein ist nur Komfort, nicht Sicherheit.

---

## Standardwert im Entwicklungsstand

Der vorbereitende Runtime-Wert ist aktuell:
- `ASTROMANAGER_LICENSE_EDITION=dev_all`

Das ist bewusst entwicklungsfreundlich und schaltet aktuell alle vorbereiteten Features frei.
Für produktive Systeme soll später die echte Lizenzquelle maßgeblich werden.
