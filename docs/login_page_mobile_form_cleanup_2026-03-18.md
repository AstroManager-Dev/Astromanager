# Login-Seite mobil bereinigt

## Problem
- Login- und Bootstrap-Form nutzten Settings-Grid-/Field-Strukturen.
- Auf Mobilgeräten wurden Felder nebeneinander gedrückt.
- Inputs wirkten optisch fremd und waren schwer bedienbar.

## Umsetzung
- Login-Seite auf eigene Card-/Form-Struktur umgestellt.
- Neues CSS-Modul `16_login.css` ergänzt.
- Passwort- und Benutzerfelder jetzt vertikal, breit und mobil sauber bedienbar.
- Admin-Benutzerverwaltung ebenfalls auf eigene, besser lesbare Formblöcke umgestellt.

## Betroffene Dateien
- `code/web/templates/pages/_login_page.html`
- `code/web/static/css/modules/16_login.css`
