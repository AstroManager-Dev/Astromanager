# Einheitlicher Seitenstart unter dem Header

## Ziel
Alle Hauptseiten sollen direkt unter dem globalen Header mit derselben Intro-Struktur beginnen.

## Umsetzung
- neues gemeinsames Include `code/web/templates/includes/_page_intro.html`
- einheitlicher Seitenkopf für Galerie, Atlas, Targets, Zentrale, Einstellungen, Logs, Admin, Dev, Datenbank und Programm-Info
- erste Inhaltsblöcke bleiben fachlich getrennt, aber der Start jeder Seite ist visuell gleich aufgebaut

## Betroffene Wirkung
- konsistenter Abstand und Aufbau direkt unter dem Header
- weniger visuelle Sprünge beim Wechsel zwischen Tabs
- Seitenkopf-Logik zentralisiert statt je Template separat verteilt
