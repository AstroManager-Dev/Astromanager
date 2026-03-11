# AstroManager Pipeline

## Zweck

Die Pipeline verarbeitet astronomische Rohdaten schrittweise von der Übernahme bis zur späteren finalen Ziel- und Stack-Darstellung.

Sie trennt bewusst zwischen:
- Rohdaten-Sync
- Indexierung
- Resolver-Anreicherung
- Kalibration
- Stacking
- Finalisierung
- UI-Darstellung

---

## Grundprinzip

Die Pipeline soll langfristig **sessionzentriert** arbeiten.

Das bedeutet:
- einzelne Sessions bleiben als eigene Einheiten erhalten
- Gruppen über mehrere Tage werden zusätzlich gebildet
- frühere Zwischen- und Endstände werden nicht still überschrieben
- Session-Stacks, Gruppen-Stacks und Mosaike werden logisch getrennt behandelt

---

## Hauptstufen

### 1. Rohdaten-Sync

Zweck:
- neue Rohdaten vom Quellsystem übernehmen
- keine doppelten Daten unnötig kopieren
- Zielordnerstruktur sauber befüllen

Wichtige Punkte:
- Prüfung auf neue oder geänderte Daten vor dem Kopieren
- keine unnötige Verdopplung in temporären Bereichen
- klare Zielstruktur auf HDD / SSD
- später sauberer Status pro übernommenem Ordner

---

### 2. Indexierung

Zweck:
- Sessions, Rohdateien und technische Metadaten in die Datenbank schreiben
- Session-Struktur aufbauen
- erste Header-Informationen erfassen

Erfasste Inhalte:
- Sessionpfade
- Zielnamen aus Quelle oder Header
- Exposure
- Gain
- Binning
- Dateianzahl
- Dateigrößen
- Header-Werte wie Objektname, RA, DEC, EXPTIME, GAIN

Ergebnis:
- Datenbank kennt Sessions und Rohdateien
- Grundlage für Resolver, Matching und Stacklogik ist vorhanden

---

### 3. Resolver-Anreicherung

Zweck:
- aus Roh-Zielnamen und Koordinaten eine belastbare Zielidentität aufbauen

Aktuelle Resolver:
- Sesame
- Wikidata
- NED
- SIMBAD
- NASA Image Library

Rollen:
- Sesame: erste Zielauflösung und Basis-Koordinaten
- Wikidata: Labels, Aliasse, Wikipedia, Typ-Labels, Distanzfelder
- NED: extragalaktische Basisdaten
- SIMBAD: Roh-Typ, Haupt-ID, Koordinaten
- NASA: Bild- und Medienbezug

Ergebnis:
- quellenbezogene Felder in `targets`
- noch keine harte Vereinheitlichung
- Grundlage für Merge und UI

---

### 4. Final-Merge

Zweck:
- aus mehreren Rohquellen eine sinnvolle finale Zielsicht erzeugen

Aktuelle finale Felder:
- `final_name`
- `final_objtype`
- `final_ra_deg`
- `final_dec_deg`
- `final_distance_value`
- `final_distance_unit`
- `final_source_summary`

Aktuelle Prioritäten:
- Name: Wikidata > NED > SIMBAD > canonical_name
- Koordinaten: SIMBAD > NED > Sesame
- Anzeige-Typ: Wikidata > NED > SIMBAD
- Distanzanzeige: normiert in Lichtjahren

Zusatzfelder:
- `distance_source`
- `distance_ref`
- `distance_ly`
- `identity_method`
- `identity_confidence`
- `coord_match_sep_arcsec`
- `constellation`

---

### 5. Kalibration

Zweck:
- passende Kalibrationsdaten zentral verwalten und zuordnen

Geplante Richtung:
- zentraler Master-Dark-Pool
- später auch Flat-Pool
- Matching nach:
  - Exposure
  - Gain
  - Binning
  - Temperatur
  - Kamera
- später Toleranzfenster statt nur exakter Gleichheit

Wichtig:
- Kalibrationsstände sollen versioniert werden
- Zuordnungen sollen nachvollziehbar bleiben
- alte Master nicht still überschreiben

---

### 6. Session-Stacks

Zweck:
- aus genau einer Session einen ersten reproduzierbaren Stack erzeugen

Eigenschaften:
- bleibt eng an eine Session gebunden
- bildet die erste verarbeitete Zwischenstufe
- dient als Grundlage für spätere Gruppen-Stacks oder Qualitätsbewertung

---

### 7. Gruppen-Stacks über mehrere Tage

Zweck:
- mehrere passende Sessions desselben Targets zusammenführen

Regeln:
- gleiche oder kompatible Parameter
- selbes Ziel
- definierte Gruppenlogik
- frühere Gesamtstände bleiben erhalten
- neue Gruppenstände werden versioniert

Nutzen:
- sichtbare Entwicklung eines Targets über mehrere Nächte
- besseres Signal-Rausch-Verhältnis
- historischer Verlauf bleibt nachvollziehbar

---

### 8. Mosaik-Logik

Zweck:
- benachbarte Sessions oder Kacheln als Mosaik verarbeiten

Wichtige Eigenschaften:
- eigener Verarbeitungspfad
- eigene Gruppierungslogik
- getrennte Behandlung von normalen Deep-Sky-Sessions
- später eigene UI-Ansicht

Sun, Moon, Startrails, Mosaik und Panorama sollen langfristig als eigene Kategorien sauber getrennt geführt werden.

---

### 9. Finalisierung

Zweck:
- aus Session-Stacks, Gruppen-Stacks oder Mosaiken finale Produkte ableiten

Später denkbare Endstufen:
- Final-Stack
- bestes Preview
- bestes Finalbild
- veröffentlichungsfähige Version
- postprocessed Version

Dabei wichtig:
- Versionierung
- Nachvollziehbarkeit
- keine stille Zerstörung früherer Stände

---

### 10. Zielzentrierte UI und Auswertung

Zweck:
- Daten nicht nur speichern, sondern pro Ziel sinnvoll darstellen

Bereits vorhanden:
- eigener Targets-Tab
- Trennung zwischen Deep-Sky-Targets und Systemzielen
- NASA-Bild
- Name, Typ, Sternbild, Koordinaten, Distanz
- Status-Informationen

Später:
- Ziel-Detailseite
- Session-Timeline
- Stack-Hierarchie
- Zielstatistiken
- Filter und Suche
- technische Detailansicht

---

## Sessionzentrierte Philosophie

Die Pipeline soll nicht global immer wieder den gesamten Datenbestand stumpf neu abarbeiten, sondern stärker von einzelnen Sessions ausgehen.

Das bedeutet langfristig:
- neue Session erkannt
- Session indexiert
- Session gematcht
- Session kalibriert
- Session-Stack erzeugt
- passende Gruppen aktualisiert
- spätere Finalprodukte gezielt neu gerechnet

Dadurch wird die Verarbeitung:
- nachvollziehbarer
- schneller
- modularer
- besser neu startbar

---

## Geplante Erweiterungen

### Qualitätsbewertung
- Fokus
- Transparenz
- Tracking
- Sternform
- Hintergrund
- Nutzbarkeit pro Session und Stack

### Resolver- und Match-Qualität
- sicherer Radiusabgleich
- Entscheidungssicherheit
- Resolver-Logik besser dokumentieren
- Fehlerfälle gezielt markieren

### VLM und Postproduktion
- Bildbewertung fertiger Stacks
- Erkennung typischer Probleme
- Bearbeitungsvorschläge
- spätere halbautomatische Finalisierung

---

## Wichtige technische Grundsätze

- Rohdaten und Finaldaten bleiben getrennt
- Quellenfelder bleiben erhalten
- Finalfelder werden neu abgeleitet
- Systemziele werden separat behandelt
- Stacks werden logisch versioniert
- Kalibrationsdaten werden zentral verwaltet
- UI zeigt bevorzugt finale und sinnvolle Felder statt Rohchaos

---

## Nächste sinnvolle Pipeline-Schritte

1. Session-Gruppierung sauber modellieren
2. Master-Dark-Pool produktiv integrieren
3. Ziel-Matching unbekannter Sessions vervollständigen
4. Stack-Hierarchie in der Datenbank abbilden
5. Gruppen-Stacks und Mosaik-Pfade ergänzen
