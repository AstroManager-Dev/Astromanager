# Auth / Rollen / Benutzerverwaltung – Grundstruktur

## Ziel
AstroManager trennt Anzeige und Schreibrechte künftig über feste Rollen und zentrale Permissions.

## Rollen
- `guest` – nicht angemeldet, nur Galerie / Sessions / Targets / Atlas / RAW / FITS
- `observer` – angemeldeter Lese-Benutzer, gleiche Sichtrechte wie Gast
- `user` – darf Workflows und Systemstatus nutzen
- `admin` – darf zusätzlich Einstellungen, Dev-Tools, Datenbank und Benutzerverwaltung öffnen

## Datenbank
Neue Migration `0004_auth_users_roles.sql`:
- `roles`
- `app_users`
- `user_roles`

Die Rollen werden direkt per Migration mit den Systemrollen `guest`, `observer`, `user`, `admin` vorbelegt.

## Web-Logik
Neue zentrale Datei `code/web/functions/auth.py`:
- Rollen- und Permission-Mapping
- aktueller Benutzerkontext
- Helper für Templates
- Route-Schutz über `require_permission(...)`
- Action-Mapping für Workflow-Buttons

## Sichtbarkeit / Schutz
- Gast / Observer sehen keine Zentrale und keine Settings
- User sehen Zentrale, Logs und Workflow-Aktionen
- Admin sieht zusätzlich Settings, Dev und DB-Bereiche
- Backend schützt sensible Routen zusätzlich mit 403

## Aktueller Auth-Stand
Noch kein echter Login-Flow.
Der aktuelle Benutzer kann vorerst über Env gesetzt werden:
- `ASTROMANAGER_AUTH_USERNAME`
- `ASTROMANAGER_AUTH_ROLE`

Wenn ein Benutzername gesetzt ist und in `app_users` existiert, werden Rollen aus der DB gelesen.
Sonst wird auf die Env-Rolle zurückgefallen.
