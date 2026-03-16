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
