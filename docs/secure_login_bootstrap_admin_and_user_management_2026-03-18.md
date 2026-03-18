# Secure Login, Bootstrap-Admin und Benutzerverwaltung

## Ziel
- Kein offenes Signup.
- Erstes Adminkonto ist fest vorbereitet (`admin`).
- Beim ersten Login muss dieses Adminkonto einmalig ein Passwort setzen.
- Danach können nur Admins weitere Benutzer anlegen, Rollen vergeben, Passwörter setzen und Benutzer aktivieren/deaktivieren.

## Datenbank
Neue Migration:
- `code/db/migrations/0005_secure_login_bootstrap.sql`

Ergänzt in `app_users`:
- `must_set_password`
- `is_builtin`
- `failed_login_attempts`
- `locked_until`
- `password_updated_at`
- `last_login_ip`

Seedet das feste Bootstrap-Adminkonto:
- Username: `admin`
- Anzeigename: `Administrator`
- Rolle: `admin`
- Passwort zunächst leer
- `must_set_password = 1`

## Web-Login
- Flask-Session mit Secret-Key aus `CONFIG_ROOT/web_secret_key.txt`
- HTTPOnly-Cookie
- SameSite=Lax
- optional `SESSION_COOKIE_SECURE` über `ASTROMANAGER_SECURE_COOKIE=1`

## Login-Flows
### 1. Erststart
Wenn noch kein aktiver Admin mit Passwort existiert:
- `/login` zeigt Admin-Bootstrap-Formular
- Passwort muss mindestens 12 Zeichen, Groß/Kleinbuchstaben und Zahl enthalten

### 2. Normale Anmeldung
- Username + Passwort
- gesperrt nach 5 Fehlversuchen für 15 Minuten
- erfolgreiche Anmeldung schreibt `last_login_at` und `last_login_ip`

### 3. Benutzerverwaltung (nur Admin)
- Benutzer anlegen
- Rolle setzen (`observer`, `user`, `admin`)
- Passwort setzen
- aktivieren/deaktivieren

## Nicht umgesetzt
- Keine öffentliche Registrierung
- Kein Passwort-Reset per E-Mail
- Keine 2FA
- Keine externen Auth-Provider
