# Login-Bereich im Kopfbereich und einfache Benutzeranzeige

## Stand
- Neben dem Einstellungs-Button wurde ein zweiter Icon-Button fuer Login/Profil eingebaut.
- Unter beiden Kopfbereich-Buttons wird jetzt ein kompakter Benutzerstatus angezeigt.
- Ohne hinterlegten Benutzer wird `Gast` und `Nicht angemeldet` gezeigt.
- Mit `ASTROMANAGER_LOGIN_USER` kann spaeter direkt ein Name eingeblendet werden.

## Technische Punkte
- `code/web/app.py`
  - `load_login_info()` liefert einfachen Login-Kontext fuer das UI.
  - neuer Route-Einstieg `/login` fuer einen vorbereiteten Login-/Profilbereich.
- `code/web/templates/includes/_topbar_brand.html`
  - Kopfbereich um Login-Icon und Benutzerstatus erweitert.
- `code/web/templates/login_page.html`
  - neue Seite fuer Login-/Profilbereich.
- `code/web/templates/pages/_login_page.html`
  - vorbereitete Login-Karte mit aktuellem Benutzerstatus.
- `code/web/static/css/app.css`
  - neue Styles fuer Icon-Buttons und Benutzerstatus im Kopfbereich.

## Env-Vorbereitung
- optional: `ASTROMANAGER_LOGIN_USER`
- optional: `ASTROMANAGER_LOGIN_HREF`

Ohne gesetzte Werte bleibt die Anzeige im Gastmodus.
