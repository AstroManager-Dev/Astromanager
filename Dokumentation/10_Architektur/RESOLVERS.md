# AstroManager Resolver

## Prinzip

Jede Quelle hat eine definierte Rolle.
Resolver schreiben zunächst quellennahe Daten.
Erst danach erfolgt der Merge.

## Sesame

### Zweck
- erste Zielauflösung
- Basis-Koordinaten
- Name-zu-Koordinaten-Verbindung

### Stärken
- astronomisch passend für Zielidentifikation
- gut für erste Koordinaten

### Grenzen
- nicht ideal für UI-Namen
- bei Sun und Moon nicht sinnvoll für finale feste Koordinaten

## Wikidata

### Zweck
- deutsche und englische Labels
- Aliasse
- Wikipedia-Bezüge
- Typ-Labels
- Distanz- und Einheitenfelder
- zusätzliche Medien- und Wissensverknüpfung

### Stärken
- gut für UI-Namen
- gut für lesbare Typen
- gut für Wikipedia-Integration

### Grenzen
- physikalische Werte nicht immer konsistent
- Suchtreffer müssen validiert werden
- QIDs müssen für UI oft weiter aufgelöst werden

## NED

### Zweck
- extragalaktische Identifikation
- präzise Koordinaten
- bevorzugter Name
- Objektklasse
- Redshift

### Stärken
- astrophysikalisch robuste Basiseinträge
- geeignet für Galaxien und extragalaktische Objekte

### Grenzen
- nicht für alles gleich gut
- Distanzinformationen nicht immer direkt im ersten Endpunkt

## SIMBAD

### Zweck
- astronomische Haupt-ID
- Roh-Typ
- Koordinaten
- klassische Objektidentität

### Stärken
- sehr gute astronomische Basis
- viele Identifikatoren
- gute Rohklassifikation

### Grenzen
- Roh-Typen sind nicht immer der gewünschte Anzeige-Typ
- Beispiel: M31 kann als AGN erscheinen, obwohl UI-seitig Spiralgalaxie sinnvoller ist

## NASA Image Library

### Zweck
- Vorschaubilder
- Detailseiten
- Asset-Manifeste
- Medienbezug für Targets

### Stärken
- schöne Zieldarstellung in der UI
- mehrere Bildvarianten
- stabile NASA-ID und Detailseite

### Grenzen
- Suchtreffer müssen stärker gefiltert werden
- erste Treffer sind nicht immer inhaltlich optimal
