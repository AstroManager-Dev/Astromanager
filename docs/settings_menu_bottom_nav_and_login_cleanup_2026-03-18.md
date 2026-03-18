# Settings, Menü, Bottom-Navigation und Login-Form Cleanup – 2026-03-18

## Inhalt
- Settings-Module rendern jetzt serverseitig sichtbar (`active`), damit Info, Admin-Module und Lock-Panels nicht durch Session-Switch-CSS verborgen werden.
- Unter gesperrten Settings-Tabs erscheint ein kompakter Hinweis, dass nur `Info` verfügbar ist.
- Bottom-Navigation wurde in ein eigenes Modul ausgelagert und vereinheitlicht.
- Menü-Einträge nutzen jetzt einen kompakten Hauptaktionsstil statt des alten uneinheitlichen Sheet-Links.
- Login-/Admin-Formulare erhielten Breiten- und Box-Sizing-Fixes für mobile Ansichten.

## Betroffene Dateien
- `code/web/templates/pages/_settings_page.html`
- `code/web/templates/pages/settings/_devices.html`
- `code/web/templates/pages/settings/_sources.html`
- `code/web/templates/pages/settings/_display.html`
- `code/web/templates/pages/settings/_system.html`
- `code/web/templates/pages/settings/_info.html`
- `code/web/templates/pages/settings/_locked_panel.html`
- `code/web/templates/includes/_menu.html`
- `code/web/static/css/modules/16_login.css`
- `code/web/static/css/modules/18_bottom_nav_cleanup.css`
- `code/web/static/css/modules/19_menu_buttons.css`
