# Changelog

## 2026-03-11  Version: 0.3.000
- Datei- und Session-Indexierung aus RAW-Ordnern abgeschlossen; Resolver-Grundlage für Targets und Constellation produktiv integriert
- Target-Final-Merge eingeführt, VizieR-TAP-Daten integriert, Distanz auf Lichtjahre harmonisiert und target_final als saubere Endstand-Tabelle aufgebaut
- VizieR-Resolver auf TAP/ADQL modernisiert, auf echten NGC2000-Katalog VII/118 umgestellt und modulare TAP-basierte Katalogauflösung eingeführt
- Constellation-Resolver modularisiert, auf bevorzugte Targets-Koordinaten mit Base-Fallback umgestellt und um gespeicherte Koordinatenquelle sowie Positionsfelder erweitert
- Wikidata-Resolver um exakten Katalog-Lookup via P528/P373 erweitert, Rate-Limit robuster gemacht und problematische Katalogobjekte wie Messier 32 und NGC 206 sauber aufgelöst
- Wikidata-Resolver um exakten Katalog-Lookup via P528/P373 erweitert, Rate-Limit-toleranter gemacht und problematische Katalogobjekte wie M32 und NGC 206 sauber aufgelöst
- Wikidata-Matching um harte Resolver-Konsistenzchecks sowie P528/P373-Kataloganker erweitert und Fallback-Display für label-lose Katalogobjekte ergänzt
- Zentrale Distanz-Harmonisierung nach Lichtjahren eingeführt und Wikidata-Resolver auf gemeinsame Distance-Normalisierung umgestellt
- Wikidata-Meta-Label-Resolver modularisiert und alte 0390-Heuristik durch saubere Label-Auflösung ersetzt
- NED-Resolver modularisiert und um zusätzliche NED-Felder erweitert; obsoleten NED-Sync-Step als Legacy markiert
- SIMBAD-Resolver auf TAP-only mit Koordinaten-Priorität umgestellt und Resolverdaten erweitert
- Obsoleten disabled Sesame-Sync-Step 0320 entfernt, da target_sesame_resolve direkt vom Resolver gepflegt wird
- Sesame-Resolver modularisiert und Alias-Speicherung in target_sesame_resolve ergänzt
- Target-Resolver-Table-Sync in commands- und targets-Module strukturiert und Base-Sync erweitert
- Zentrale Target-Namenslogik auf Klassenpriorität umgestellt und Messier vor NGC/IC im Final-Name-Merge priorisiert
- Zentrale Target-Namenslogik angelegt und Katalognamen-Normalisierung für Final-Name-Merge ergänzt
- Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
- Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
- Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
- target_constellation_resolve auf base-resolve als Koordinatenquelle umgestellt und constellation_name plus constellation_code erfolgreich aktiviert
- target_constellation_resolve auf constellation_name plus constellation_code umgestellt und Resolver auf saubere Seitentabelle umgebaut
- Web-UI in Base-Template, Seiten-Partials, separates Menü sowie ausgelagerte CSS- und JS-Dateien modularisiert
- Web-UI Header mit Logo links und Burger-Menü für Übersicht, Targets und DB
- Web-UI erweitert: Button-Action-Handler ausgelagert, Index Sessions startet Index plus Targets, Web-Importfehler behoben und Live-Fortschritt für laufende Indexierung mit Log-Tailing sowie Fortschrittsbalken vorbereitet
- DB Backup Manager überarbeitet: vollständiges interaktives Menü mit sichtbarer Backup-Auswahl für Restore und Löschen, 0-zurück-Navigation in Untermenüs, Sicherheitsabfragen für Restore, Undo, Reset und Delete sowie automatisches Backup vor DB-Reset
- Dynamisches DB-Reset-Skript ergänzt: Never-Reset-Tabellen per Konfigurationsdatei definiert, Dry-Run für Tabellenlöschung geprüft, Reset aller übrigen Tabellen inklusive Sequenz-Rücksetzung vorbereitet
- AstroManager-VLM erweitert: lokales Ollama-Backend mit Text-, Code- und Vision-Modellen angebunden, VLM-Service als eigener Docker-Dienst ergänzt, Trainingsbeispiele per API speicherbar gemacht, Web-Fetch/Ingest/Knowledge-Search mit lokaler Wissensbasis eingebaut, HTML-Extraktion für Doku-Seiten um Script- und Style-Filter verbessert
- Index-Resolve stabilisiert: OpenNGC mit zentraler Source-Konfiguration und DB-gestütztem Cache/Fallback eingebunden, 0900_target_resolve_sessions wieder korrekt verkabelt, kanonische Target-Wiederverwendung für Session-Targets verifiziert, Dublettenbildung M 31 versus m31 im Resolve-Pfad verhindert
- Index-Workflow auf index.sh Dispatcher mit Blocklogik umgebaut, vierstellige Step-Nummerierung eingeführt, Cleanup-Workflow ohne aktive Steps sauber behandelt, Dedupe im Index deaktiviert
- Patch und Minor Skript verbessert
- Resolver-Architektur erweitert: Query-/Match-Kontext für Resolver-Tabellen ergänzt, Sesame SIMBAD und NED auf echte Side-Table-Resolver umgestellt, VizieR gehärtet, Merge-Steps 0700 und 1100 vorerst deaktiviert
- Fix platesolve pipeline: wcsinfo parsing, field footprint DB update, target resolve with OpenNGC and solved session matching
- Index-Workflow auf inkrementellen Standardlauf umgestellt und --full für vollständigen Rescan ergänzt
- Target-Resolver als Auto-Controller mit Step-Dateien umgesetzt
- Index-Workflow in Auto-Controller und Step-Dateien aufgeteilt
- Index-Controller auf automatische Step-Erkennung umgestellt
- DB-Migration 0004 für Dwarf-Ableitungen und Raw-File-Klassifikation ergänzt
- Backfill-Migration 0003 für bestehende Dwarf-3-Session-Klassifikation ergänzt
- DB-Migration 0002 für Dwarf-3-Session-Klassifikation ergänzt
- Backup-Logik für zusammengeführtes Changelog im Backup ergänzt

## 2026-03-08  Version: 0.2.000

- Datenquellenmodell und Release-Basis konsolidiert

- Release-Skripte für Patch- und Minor-Versionierung angelegt

- Backup-Skript um Versionsnamen erweitert

## 2026-03-08  Version: 0.1.000

- Ausgangsbasis definiert

- Targets aus mehreren Quellen auflösbar

- Deep-Sky und Systemziele in der UI getrennt

- NASA-Medien integriert

- Final-Merge implementiert

- Qualitätsfelder ergänzt

- Dokumentationsstruktur zentralisiert

- Versionierung eingeführt

