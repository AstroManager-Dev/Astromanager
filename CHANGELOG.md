# Changelog

## 2026-03-15  Version: 0.4.013
- Backup-Stand erzeugt
- Projektversion: 0.4.013
- Schema-Version: 2
- Galerie und Session-Unterseiten auf echte Beobachtungssessions begrenzt: nur light_session für deepsky, moon und sun; Kalibrierungs-Sessions werden nicht mehr angezeigt
- Galerie mit echten Sessions aus der DB verbunden: Monatsgruppen, Session-Targets, Preview-Fallback und Session-Unterseite /sessions/<id> ergänzt
- Galerie- und Session-Templates wie bei Targets modularisiert: Monatsblöcke, Session-Karten, Bild- und Metablöcke in eigene Include-Dateien ausgelagert
- Bottom-Navigation auf Target-Unterseiten vollständig repariert: Tab-Buttons führen zur Hauptseite zurück und auf /targets/<id> wird Targets als aktiver Navigationspunkt markiert
- Target-Detailseite bereinigt: Titelblock vereinfacht, Session-Anzahl unter die Header-Card verschoben und Session-Preview-Fallback ergänzt
- Target-Detailseite repariert: Session-Gruppierung auf session_items umgestellt und Session-Preview mit nopic-Fallback ergänzt
- Target-Detailseite repariert: Session-Gruppierung in Jinja auf session_items umgestellt und 500-Fehler auf /targets/<id> behoben
- Target-Detailseite repariert, Header-Card und Session-Buttons modularisiert sowie Dwarf-Preview, EXP, Gain und Gesamtbelichtungsdauer je Session ergänzt
- Targets-Templates modularisiert: Deep-Sky- und Solarsystem-Blöcke ausgelagert, gemeinsame Target-Karte eingeführt und Bildblock als eigenes Include im pages/targets-Unterordner getrennt
- Targets-Ansicht bereinigt, Introbereich entfernt und Sun & Moon in Solarsystem-Targets umbenannt
- Legacy-Survey-Resolver ergänzt, SkyView-No-Data-Prüfung eingebaut, Bild-Fachlogik zentralisiert und Target-Bildfallback auf Session → Legacy → SkyView → NASA umgestellt
- SkyView-Fallback verifizieren, Resolver-Struktur erweitern, Target-Bildlogik härten
- Dev-Bereich für Core-Backup/Restore und ZIP-Import erweitert: Kern-Backups für code/scripts/Versionsdateien, Archiv mit Download/Restore, letztes Backup zurückspielen und ZIP einspielen mit Überschreiben.
- Target-Webbildfolge auf Session -> SkyView -> NASA umgestellt und SkyView-Resolver um Survey-Auswahl je Objekttyp sowie dynamische FOV-Groesse erweitert.
- Legacy-Survey als eigener Target-Bildresolver mit eigener Migration/Steps/Tabelle ergänzt, SkyView-No-Data-Guard eingebaut und Bild-Fachlogik in zentrale Python-Module ausgelagert.


## 2026-03-14  Version: 0.4.000
- Web-UI konzeptionell auf mobile Astro-App umgestellt: Deep-Sky-Design, Logo-Integration, Bottom-Navigation, Live-Status, Dev-/Admin-Bereiche und Android-WebView-Richtung für den Raspberry Pi 5 AstroManager.
- Designanpassungen
- Mobile-App-UI modernisiert: Deep-Sky-Design mit Glow-Effekten, Pop-up-/Bottom-Sheet-Menü, Dev-Bereich für Backups/SQL-Dumps/Organizer, jobbezogenes Live-Refresh per Button-Klick und Admin/Technik sauber aus dem Hauptfluss getrennt.
- Architektur fuer getrennte Geraetetypen und reale Device-Instanzen festgelegt; device_sources bleibt fuer Typ-Defaults, konkrete Hosts/Credentials kommen kuenftig in eigene Device-Instanz-Tabelle
- RAW-Sync Fehlerpfad analysiert; Vorbereitung fuer harten Abbruch bei fehlender remote_inventory/sync_plan/fetch_result und korrekten Error-Status statt false ok
- RAW-Sync Live-Fortschritt vorbereitet; fetch_sync.py fuer laufende progress-Zeilen erweitert und progress_runtime.py fuer RAW-Progress-Auswertung angepasst
- RAW-Sync, Job-Tracking und Zeitzonen fuer job_runs bereinigt; Vorbereitung fuer Live-Fortschritt im RAW-Sync
- RAW-Sync, Index-Trigger und Web-UI-Anbindung weiter angepasst; aktuelles Backup fuer naechste Analyse erzeugen
- RAW-Sync fuer DWARF3 produktiv integriert, Root-Pattern-Matching fuer DWARF_RAW_TELE*, DWARF_DARK und CALI_FRAME korrigiert, Dry-Run/Quoting/common.sh-Fehler behoben, neue RAW-Sessions und Darks werden korrekt erkannt und synchronisiert, Index-Workflow um 9999_trigger_targets.sh erweitert
- CHANGELOG.unreleased.md auf das Skriptformat bereinigt und RAW-Sync-Release-Stand konsistent abgeschlossen
- Modularen RAW-Sync für DWARF3 aufgebaut, Root-Pattern-Matching für DWARF_RAW_TELE*, DWARF_DARK und CALI_FRAME korrigiert, Dry-Run/Quoting/common.sh-Fehler behoben, bekannte ok-Dateien mit unbekannter Remote-mtime werden nicht mehr fälschlich ersetzt, neue RAW-Sessions und Darks werden jetzt korrekt erkannt und synchronisiert, 0060_trigger_index.sh ergänzt

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

