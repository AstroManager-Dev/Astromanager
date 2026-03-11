0.2.039 | 2026-03-11 17:44:06 | Target-Final-Merge eingeführt, VizieR-TAP-Daten integriert, Distanz auf Lichtjahre harmonisiert und target_final als saubere Endstand-Tabelle aufgebaut
0.2.038 | 2026-03-11 16:53:40 | VizieR-Resolver auf TAP/ADQL modernisiert, auf echten NGC2000-Katalog VII/118 umgestellt und modulare TAP-basierte Katalogauflösung eingeführt
0.2.037 | 2026-03-11 16:00:27 | Constellation-Resolver modularisiert, auf bevorzugte Targets-Koordinaten mit Base-Fallback umgestellt und um gespeicherte Koordinatenquelle sowie Positionsfelder erweitert
0.2.036 | 2026-03-11 15:47:42 | Wikidata-Resolver um exakten Katalog-Lookup via P528/P373 erweitert, Rate-Limit robuster gemacht und problematische Katalogobjekte wie Messier 32 und NGC 206 sauber aufgelöst
0.2.035 | 2026-03-11 15:42:57 | Wikidata-Resolver um exakten Katalog-Lookup via P528/P373 erweitert, Rate-Limit-toleranter gemacht und problematische Katalogobjekte wie M32 und NGC 206 sauber aufgelöst
0.2.034 | 2026-03-11 13:48:59 | Wikidata-Matching um harte Resolver-Konsistenzchecks sowie P528/P373-Kataloganker erweitert und Fallback-Display für label-lose Katalogobjekte ergänzt
0.2.033 | 2026-03-11 12:44:03 | Zentrale Distanz-Harmonisierung nach Lichtjahren eingeführt und Wikidata-Resolver auf gemeinsame Distance-Normalisierung umgestellt
0.2.032 | 2026-03-11 12:16:45 | Wikidata-Meta-Label-Resolver modularisiert und alte 0390-Heuristik durch saubere Label-Auflösung ersetzt
0.2.031 | 2026-03-11 11:23:01 | NED-Resolver modularisiert und um zusätzliche NED-Felder erweitert; obsoleten NED-Sync-Step als Legacy markiert
0.2.030 | 2026-03-10 23:49:07 | SIMBAD-Resolver auf TAP-only mit Koordinaten-Priorität umgestellt und Resolverdaten erweitert
0.2.029 | 2026-03-10 22:15:26 | Obsoleten disabled Sesame-Sync-Step 0320 entfernt, da target_sesame_resolve direkt vom Resolver gepflegt wird
0.2.028 | 2026-03-10 22:05:57 | Sesame-Resolver modularisiert und Alias-Speicherung in target_sesame_resolve ergänzt
0.2.027 | 2026-03-10 21:29:44 | Target-Resolver-Table-Sync in commands- und targets-Module strukturiert und Base-Sync erweitert
0.2.026 | 2026-03-10 20:58:34 | Zentrale Target-Namenslogik auf Klassenpriorität umgestellt und Messier vor NGC/IC im Final-Name-Merge priorisiert
0.2.025 | 2026-03-10 20:42:02 | Zentrale Target-Namenslogik angelegt und Katalognamen-Normalisierung für Final-Name-Merge ergänzt
0.2.024 | 2026-03-10 20:28:45 | Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
0.2.023 | 2026-03-10 20:20:32 | Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
0.2.022 | 2026-03-10 20:17:01 | Target-Namenslogik in zentrale Python-Helperstruktur unter lib/py ausgelagert
0.2.021 | 2026-03-10 18:34:28 | target_constellation_resolve auf base-resolve als Koordinatenquelle umgestellt und constellation_name plus constellation_code erfolgreich aktiviert
0.2.020 | 2026-03-10 17:59:49 | target_constellation_resolve auf constellation_name plus constellation_code umgestellt und Resolver auf saubere Seitentabelle umgebaut
0.2.019 | 2026-03-10 16:09:50 | Web-UI in Base-Template, Seiten-Partials, separates Menü sowie ausgelagerte CSS- und JS-Dateien modularisiert
0.2.018 | 2026-03-10 15:55:07 | Web-UI Header mit Logo links und Burger-Menü für Übersicht, Targets und DB
0.2.017 | 2026-03-10 12:55:32 | Web-UI erweitert: Button-Action-Handler ausgelagert, Index Sessions startet Index plus Targets, Web-Importfehler behoben und Live-Fortschritt für laufende Indexierung mit Log-Tailing sowie Fortschrittsbalken vorbereitet
0.2.016 | 2026-03-10 11:12:36 | DB Backup Manager überarbeitet: vollständiges interaktives Menü mit sichtbarer Backup-Auswahl für Restore und Löschen, 0-zurück-Navigation in Untermenüs, Sicherheitsabfragen für Restore, Undo, Reset und Delete sowie automatisches Backup vor DB-Reset
0.2.015 | 2026-03-10 08:19:42 | Dynamisches DB-Reset-Skript ergänzt: Never-Reset-Tabellen per Konfigurationsdatei definiert, Dry-Run für Tabellenlöschung geprüft, Reset aller übrigen Tabellen inklusive Sequenz-Rücksetzung vorbereitet
0.2.014 | 2026-03-09 23:00:24 | AstroManager-VLM erweitert: lokales Ollama-Backend mit Text-, Code- und Vision-Modellen angebunden, VLM-Service als eigener Docker-Dienst ergänzt, Trainingsbeispiele per API speicherbar gemacht, Web-Fetch/Ingest/Knowledge-Search mit lokaler Wissensbasis eingebaut, HTML-Extraktion für Doku-Seiten um Script- und Style-Filter verbessert
0.2.013 | 2026-03-09 20:02:54 | Index-Resolve stabilisiert: OpenNGC mit zentraler Source-Konfiguration und DB-gestütztem Cache/Fallback eingebunden, 0900_target_resolve_sessions wieder korrekt verkabelt, kanonische Target-Wiederverwendung für Session-Targets verifiziert, Dublettenbildung M 31 versus m31 im Resolve-Pfad verhindert
0.2.012 | 2026-03-09 18:21:22 | Index-Workflow auf index.sh Dispatcher mit Blocklogik umgebaut, vierstellige Step-Nummerierung eingeführt, Cleanup-Workflow ohne aktive Steps sauber behandelt, Dedupe im Index deaktiviert
0.2.011 | 2026-03-09 17:10:12 | Patch und Minor Skript verbessert
0.2.010 | 2026-03-09 16:58:52 | Resolver-Architektur erweitert: Query-/Match-Kontext für Resolver-Tabellen ergänzt, Sesame SIMBAD und NED auf echte Side-Table-Resolver umgestellt, VizieR gehärtet, Merge-Steps 0700 und 1100 vorerst deaktiviert
0.2.009 | 2026-03-09 00:04:18 | Fix platesolve pipeline: wcsinfo parsing, field footprint DB update, target resolve with OpenNGC and solved session matching
0.2.008 | 2026-03-08 16:34:24 | Index-Workflow auf inkrementellen Standardlauf umgestellt und --full für vollständigen Rescan ergänzt
0.2.007 | 2026-03-08 13:48:00 | Target-Resolver als Auto-Controller mit Step-Dateien umgesetzt
0.2.006 | 2026-03-08 13:14:58 | Index-Workflow in Auto-Controller und Step-Dateien aufgeteilt
0.2.005 | 2026-03-08 13:12:05 | Index-Controller auf automatische Step-Erkennung umgestellt
0.2.004 | 2026-03-08 12:18:28 | DB-Migration 0004 für Dwarf-Ableitungen und Raw-File-Klassifikation ergänzt
0.2.003 | 2026-03-08 12:05:29 | Backfill-Migration 0003 für bestehende Dwarf-3-Session-Klassifikation ergänzt
0.2.002 | 2026-03-08 12:02:33 | DB-Migration 0002 für Dwarf-3-Session-Klassifikation ergänzt
0.2.001 | 2026-03-08 11:07:04 | Backup-Logik für zusammengeführtes Changelog im Backup ergänzt
