# Benutzerbezogene FITS-Viewer-Presets

## Ziel
Zusätzlich zu den globalen Systempresets können eingeloggte Benutzer eigene FITS-Viewer-Presets speichern, überschreiben und löschen. Gäste erhalten keine Schreibfunktionen.

## Datenmodell
Neue Migration `0010_user_fits_viewer_presets.sql` mit eigener Tabelle `user_fits_viewer_presets`.

Gespeichert werden pro Benutzer:
- `preset_key`
- `label`
- `debayer_mode`
- `stretch_mode`
- `black_value`
- `white_value`
- `gamma_value`
- Sortierung und Zeitstempel

Systempresets bleiben weiter in `fits_viewer_presets`.

## UI-Verhalten
- Preset-Auswahl unter dem Bild, nicht mehr innerhalb der Render-Einstellungen
- Button `Preset speichern` öffnet einen Dialog mit Namen und Speichern-Button
- Wenn ein eigenes Preset aktiv ist, fragt Speichern vor dem Überschreiben nach `ja/nein`
- Löschen-Button nur bei eigenen Presets sichtbar
- Löschen fragt vor dem Absenden noch einmal nach

## Rechte
- Gäste: keine Speicherung, kein Löschen
- eingeloggte Benutzer mit echter `user_id`: eigene Presets speichern/überschreiben/löschen

## Technische Hinweise
- Userpresets werden zusätzlich zu den Systempresets geladen
- Eigene Presets werden im Dropdown mit `• Eigenes` markiert
- FITS-Auto-Logik bleibt unverändert und basiert weiterhin auf den Systempreset-Regeln
