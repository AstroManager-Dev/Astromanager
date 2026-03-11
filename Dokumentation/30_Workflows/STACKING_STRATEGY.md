# AstroManager Stacking Strategy

## Ziel

Die Stacking-Logik soll sessionzentriert, versioniert und nachvollziehbar arbeiten.

## Grundstufen

### 1. Roh-Session
Die unverarbeitete Sitzung mit Rohframes.

### 2. Session-Stack
Stack aus genau einer Session.

### 3. Gruppen-Stack
Stack aus mehreren Sessions eines Targets mit passenden Parametern.

### 4. Mosaik-Stack
Spezielle Verarbeitung mehrerer benachbarter Sessions oder Kacheln.

### 5. Final-Stack
Ausgewähltes Endprodukt für ein Ziel.

## Mehrtages-Logik

Wenn mehrere Sessions desselben Targets mit passenden Parametern vorliegen:
- Session-Stacks einzeln behalten
- zusätzlich Gruppen-Stack über mehrere Tage bilden
- frühere Gruppen- oder Finalstände nicht überschreiben
- neue Versionen zusätzlich anlegen

## Master-Dark-Pool

Kalibrationslogik soll zentral arbeiten:
- Zuordnung nach Exposure
- Gain
- Binning
- Temperatur
- Kamera
- später Toleranzfenster

Master-Darks sollen versioniert und nachvollziehbar zugeordnet werden.

## Mosaike

Mosaike werden nicht als normale Deep-Sky-Session behandelt, sondern als eigener Verarbeitungspfad:
- Erkennung von Kachelgruppen
- Beziehung zwischen Kachel und Gesamtmosaik
- eigener Stack-Typ
- eigene UI-Darstellung
