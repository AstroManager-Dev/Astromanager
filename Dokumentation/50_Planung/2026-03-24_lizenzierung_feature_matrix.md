# AstroManager – Feature-Matrix für Free, Basic, Plus und Pro
Stand: 2026-03-24

## Ziel

Diese Matrix definiert die fachliche Freigabelogik für das spätere Lizenzmodell.

Wichtig:
- Die Matrix ist die zentrale Produktlogik.
- Nicht jedes UI-Detail wird lizenziert.
- Lizenziert werden echte Nutzwert- oder Tiefenmodule.

---

## Editionslogik

### Free
Ziel:
- kennenlernen
- importieren
- ansehen
- prüfen, ob Gerät und Daten passen

### Basic
Ziel:
- produktiver Kernbetrieb
- verwalten
- verarbeiten
- stacken

### Plus
Ziel:
- planen
- bewerten
- entscheiden

### Pro
Ziel:
- tiefe Atlas-, Daten- und Analysefunktionen
- eigene Bilddaten im Atlas
- Coverage, Mosaik und erweiterte Forecast-/KI-Schicht

---

## Feature-Codes

### Core
- `core.import`
- `core.viewer`
- `core.targets`
- `core.sessions`
- `core.atlas_basic`
- `core.stacking`

### Plus
- `plus.progress`
- `plus.planning`
- `plus.visibility`
- `plus.recommendations`
- `plus.weather_basic`
- `plus.atlas_filters`

### Pro
- `pro.atlas_imagery`
- `pro.footprints`
- `pro.coverage`
- `pro.forecast_advanced`
- `pro.mosaic_progress`
- `pro.ai_tools`

---

## Zuordnung nach Edition

### Free
Freigeschaltet:
- Import und Quellenzugriff
- Viewer
- Targets
- Sessions
- Atlas Basis

Nicht freigeschaltet:
- Siril-Stacking
- Planung
- Sichtbarkeiten
- Wetter
- Bilddaten-Layer im Atlas

### Basic
Freigeschaltet zusätzlich zu Free:
- Siril-Stacking

Kernaussage:
- Free sieht und testet
- Basic arbeitet produktiv

### Plus
Freigeschaltet zusätzlich zu Basic:
- Target-Fortschritt
- Planungskalender
- Sichtbarkeiten
- Empfehlungen
- Wetter Basis
- Atlas-Planungsfilter

Kernaussage:
- Plus macht AstroManager zum echten Planungswerkzeug

### Pro
Freigeschaltet zusätzlich zu Plus:
- Atlas mit Bilddaten
- Session-Footprints
- Coverage und Mosaikabdeckung
- erweiterter Astro-Forecast
- Mosaik- und Kanalfortschritt
- spätere KI-Analyse und Postproduktion

Kernaussage:
- Pro ist die tiefe Daten- und Analyseebene

---

## UI-Beispiele

### Atlas
- Free/Basic: Grundatlas
- Plus: Sichtbarkeits- und Planungsfilter
- Pro: Bilddaten, Footprints, Coverage

### Planung
- Free/Basic: keine echte Planungslogik
- Plus: Planungskalender, Sichtbarkeit, Empfehlungen
- Pro: vertiefte Forecast- und Mosaikverknüpfung

### Wetter
- Plus: Basis-Wetter
- Pro: Astro-Forecast erweitert

### Bilddaten
- Pro exklusiv:
  - eigene Bilddaten im Atlas
  - Session-Footprints
  - Coverage-Layer
  - spätere Himmelsatlas-Ansicht aus eigenen Daten

---

## Bewusst nicht als Einzel-Lizenzfeature gedacht

Nicht aufsplitten in viele kleine Add-ons:
- kleine UI-Politur
- allgemeine Bugfixes
- gewöhnliche Layoutverbesserungen
- einfache Standardlistenfilter

Die Außenlogik soll verständlich bleiben:
- Free
- Basic
- Plus
- Pro

---

## Nächste technische Schritte

1. neue Module beim Bau sofort einem Feature-Code zuordnen
2. Guards zentral halten
3. keine Fachlogik mit Editionsnamen vermischen
4. später signierte Lizenzdatei ergänzen
