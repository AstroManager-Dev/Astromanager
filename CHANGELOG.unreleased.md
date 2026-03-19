0.4.039 | 2026-03-19 09:52:08 | RAW-Sync auf device_instances umgestellt, PNG/JPEG/TIFF/JSON Sync aktiviert, Settings Quellen stabilisiert und Container-User auf 1000:1000 gesetzt
0.4.038 | 2026-03-19 09:15:39 | RAW-Sync auf device_instances umgestellt, DB-Extensions/Overrides aktiv und Workflow 0030/0040/9999 repariert
0.4.037 | 2026-03-19 08:52:10 | Settings Quellen: device_sources Defaults + device_instances DB/UI vorbereitet, Web-500 in settings behoben
0.4.036 | 2026-03-19 08:43:20 | db erweiterung
0.4.035 | 2026-03-18 18:49:02 | Moon/Sun-Infos, Standorte, Session-Detail-UI kompakter
0.4.034 | 2026-03-18 15:39:18 | Bottom-Navigation per Grid-Wrapper stabilisiert und Button-Set-Anbindung korrigiert
0.4.033 | 2026-03-18 13:30:57 | Settings-Inhalte repariert, Lock-Hinweise ergänzt sowie Menü-, Bottom-Navigation- und Login-UI bereinigt
0.4.032 | 2026-03-18 11:47:39 | Login-Seite mobil bereinigt und 403-Zugriffsseite für gesperrte Bereiche ergänzt
0.4.031 | 2026-03-18 11:03:48 | Web-Secret-Key auf /runtime umgestellt, sicherer Login mit Admin-Bootstrap ergänzt und Release-Skripte auf zentrales backup.sh vereinheitlicht
0.4.030 | 2026-03-18 09:44:08 | Test Python Release Tool
0.4.029 | 2026-03-18 09:19:56 | Benutzerverwaltung und Rollenbasis eingeführt, Login-Bereich vorbereitet und Header-Nutzeranzeige verschlankt
0.4.028 | 2026-03-18 08:45:03 | Login-Bereich eingeführt, kompakte Topbar-Nutzeranzeige ergänzt und Font Awesome Icons vorbereitet
0.4.027 | 2026-03-18 08:00:51 | Test Release-Skript mit backup.sh
0.4.026 | 2026-03-18 07:51:07 | Test neuer Backup-Aufruf
0.4.025 | 2026-03-18 07:21:56 | Button-System in eigenes CSS-Modul ausgelagert und kompakte Hauptaktionsbuttons angeglichen
0.4.024 | 2026-03-17 20:13:16 | FITS-Viewer: DB-Presets, Slider-Steuerung, WebP-Previews und Preset-Sync im RAW-Detail repariert
0.4.023 | 2026-03-17 17:34:36 | feat: CSS-Modul-Loader integriert und RAW-Listen-CSS modular eingebunden
0.4.022 | 2026-03-17 13:29:03 | Settings Info als eigenen Tab ergänzt und Minor-Log im Info-Bereich eingebunden
0.4.021 | 2026-03-17 12:51:19 | Target-Detail Resolver-Modul kompakter als adaptives Grid aufgebaut
0.4.020 | 2026-03-17 00:30:42 | RAW-Dateiliste und RAW-Datei-Detailseite weiter integriert, FITS-Viewer-Vorstufe mit Debayer-Metadaten eingebunden und RAW-Zugriff pro Session ausgebaut; Light-Zählung und FITS-Preview-Rendering werden im nächsten Patch fertiggestellt.
0.4.019 | 2026-03-17 00:18:52 | RAW-Dateiliste und RAW-Datei-Detailseite für Sessions angebunden, Download pro RAW-Datei ergänzt, FITS-Viewer-Grundlage mit Debayer-Vorbereitung und Metadatenanzeige eingebaut; Light-Zählung und Vorschau-Layout werden im nächsten Schritt nachgezogen.
0.4.018 | 2026-03-16 23:36:06 | Session-Seite um RAW-Verlinkung ergänzt: Lights-Bereich mit Einstieg in die RAW-Dateiliste aufgebaut, Light-Erkennung über source_subtype korrigiert, RAW-Dateiliste mit Verlinkung auf einzelne RAW-Datei-Seiten und Download-Möglichkeit ergänzt.
0.4.017 | 2026-03-16 23:01:10 | Target-Detailseite neu geordnet: Name vor Bild, Meta unter dem Bild und Bottom-Navigation auf Targets korrigiert. Session-Detailseite modularisiert und Session-Struktur mit Session-Bild, Session-Metadaten sowie Teleskop-/AstroManager-Modulen ausgebaut.
0.4.016 | 2026-03-16 13:42:26 | Targets-Layout finalisiert: Deep-Sky-CTA neben Distanz gesetzt, Solar-System-Targets ohne RA/DEC/NASA bereinigt und zusätzlicher Bottom-Safe-Space gegen abgeschnittenen letzten Eintrag ergänzt
0.4.015 | 2026-03-16 08:27:09 | Web-Refactor vorbereitet: app.py verschlankt und Kernfunktionen in code/web/functions in kleine Fachmodule für Programm-Info, Datenbank, Status, Targets und Galerie ausgelagert; Header-Version und Programm-Info-Templates zusätzlich bereinigt
0.4.014 | 2026-03-16 07:54:43 | Header-Version ergänzt: Unter DeepSky Sessions wird die Projektversion klein und dezent als V. x.x.x aus VERSION eingeblendet; Header als Include-Modul angebunden und Styling für die Versionszeile ergänzt
0.4.013 | 2026-03-16 07:47:25 | Header-Version ergänzt: Unter DeepSky Sessions wird die Projektversion klein und dezent als V. x.x.x aus VERSION eingeblendet; Header als Include-Modul angebunden und Styling für die Versionszeile ergänzt
0.4.012 | 2026-03-15 20:27:45 | Galerie mit echten Sessions aus der DB verbunden: Monatsgruppen, Session-Targets, Preview-Fallback und Session-Unterseite /sessions/<id> ergänzt
0.4.011 | 2026-03-15 20:13:19 | Galerie- und Session-Templates wie bei Targets modularisiert: Monatsblöcke, Session-Karten, Bild- und Metablöcke in eigene Include-Dateien ausgelagert
0.4.010 | 2026-03-15 18:37:41 | Bottom-Navigation auf Target-Unterseiten vollständig repariert: Tab-Buttons führen zur Hauptseite zurück und auf /targets/<id> wird Targets als aktiver Navigationspunkt markiert
0.4.009 | 2026-03-15 18:02:46 | Target-Detailseite bereinigt: Titelblock vereinfacht, Session-Anzahl unter die Header-Card verschoben und Session-Preview-Fallback ergänzt
0.4.008 | 2026-03-15 17:43:33 | Target-Detailseite repariert: Session-Gruppierung auf session_items umgestellt und Session-Preview mit nopic-Fallback ergänzt
0.4.007 | 2026-03-15 17:26:53 | Target-Detailseite repariert: Session-Gruppierung in Jinja auf session_items umgestellt und 500-Fehler auf /targets/<id> behoben
0.4.006 | 2026-03-15 17:14:33 | Target-Detailseite repariert, Header-Card und Session-Buttons modularisiert sowie Dwarf-Preview, EXP, Gain und Gesamtbelichtungsdauer je Session ergänzt
0.4.005 | 2026-03-15 16:29:46 | Targets-Templates modularisiert: Deep-Sky- und Solarsystem-Blöcke ausgelagert, gemeinsame Target-Karte eingeführt und Bildblock als eigenes Include im pages/targets-Unterordner getrennt
0.4.004 | 2026-03-15 15:57:29 | Targets-Ansicht bereinigt, Introbereich entfernt und Sun & Moon in Solarsystem-Targets umbenannt
0.4.003 | 2026-03-15 15:47:09 | Legacy-Survey-Resolver ergänzt, SkyView-No-Data-Prüfung eingebaut, Bild-Fachlogik zentralisiert und Target-Bildfallback auf Session → Legacy → SkyView → NASA umgestellt
0.4.002 | 2026-03-15 15:12:36 | SkyView-Fallback verifizieren, Resolver-Struktur erweitern, Target-Bildlogik härten
0.4.001 | 2026-03-14 10:18:16 | Dev-Bereich für Core-Backup/Restore und ZIP-Import erweitert: Kern-Backups für code/scripts/Versionsdateien, Archiv mit Download/Restore, letztes Backup zurückspielen und ZIP einspielen mit Überschreiben.
