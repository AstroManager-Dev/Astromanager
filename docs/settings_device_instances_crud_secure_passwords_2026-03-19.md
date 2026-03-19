# Settings: Geräteinstanzen als CRUD-Modul mit sicheren Passwörtern

Stand: 2026-03-19

## Ziel

Die Geräteverwaltung wird aus dem bisherigen read-only Zustand in eine echte modulare Konfiguration überführt.

## Umsetzung

- Bereich `Geräte` ist jetzt der primäre Ort für die Konfiguration.
- Device-Sources werden dort als reiner Info-Block oberhalb der Konfiguration angezeigt.
- Source-Details sind als platzsparende Collapsibles aufgebaut.
- Geräteinstanzen können direkt in der Settings-UI angelegt, bearbeitet und gelöscht werden.
- Neue Instanzen unterstützen:
  - Auswahl einer vorhandenen Source
  - `anonymous` oder `login`
  - Host, Port, Timeout
  - optionale Overrides für Remote-Root und Extensions
  - Aktiv-/Standardstatus
- Bestehende Instanzen sind pro Karte editierbar und löschbar.

## Passwortablage

Für Gerätezugänge werden Passwörter nicht mehr im Klartext gespeichert.

- Neue Runtime-Key-Datei: `/runtime/device_credentials.key`
- Speicherung in DB-Feld `device_instances.password_enc`
- Bestehende Werte aus `password_text` werden per Migration übernommen
- RAW-Sync entschlüsselt erst beim Laden der aktiven Instanz

## Struktur

- Verschlüsselung zentral in `astromanager.security.device_credentials`
- Settings-CRUD zentral in `code/web/functions/settings_devices.py`
- Templates in kleine Settings-Module getrennt
- eigenes CSS-Modul für Geräteformulare und Collapsibles

## Dry-Run / Testgedanke

Sinnvoller Prüflauf nach Einspielen:

1. `astroctl db init`
2. Settings öffnen
3. neue Geräteinstanz mit `anonymous` anlegen
4. bestehende Instanz auf `login` umstellen
5. `astroctl raw sync --dry-run`

Dabei darf kein Klartext-Passwort mehr direkt in der DB liegen.
