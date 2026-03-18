from __future__ import annotations

import os
import secrets
import sqlite3
from functools import wraps
from typing import Any, Callable

from flask import abort, g, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db_conn, db_table_exists

ROLE_ORDER = {"guest": 0, "observer": 1, "user": 2, "admin": 3}
ROLE_LABELS = {
    "guest": "Gast",
    "observer": "Observer",
    "user": "User",
    "admin": "Admin",
}
PERMISSIONS_BY_ROLE: dict[str, set[str]] = {
    "guest": {
        "view_gallery", "view_sessions", "view_targets", "view_atlas", "view_raw_files", "view_fits_viewer", "view_login", "view_settings_info",
    },
    "observer": {
        "view_gallery", "view_sessions", "view_targets", "view_atlas", "view_raw_files", "view_fits_viewer", "view_login", "view_settings_info",
    },
    "user": {
        "view_gallery", "view_sessions", "view_targets", "view_atlas", "view_raw_files", "view_fits_viewer", "view_login", "view_settings_info",
        "view_overview", "run_workflows", "view_system_status", "view_logs",
    },
    "admin": {
        "view_gallery", "view_sessions", "view_targets", "view_atlas", "view_raw_files", "view_fits_viewer", "view_login", "view_settings_info",
        "view_overview", "run_workflows", "view_system_status", "view_logs",
        "manage_settings", "manage_users", "view_database", "manage_dev_tools",
    },
}
ACTION_PERMISSIONS = {
    "raw_sync": "run_workflows",
    "index_sessions": "run_workflows",
    "masterdarks": "run_workflows",
    "siril_session": "run_workflows",
    "siril_group": "run_workflows",
    "status": "view_system_status",
    "backup_create": "manage_dev_tools",
    "backup_restore_latest": "manage_dev_tools",
    "sql_dump": "manage_dev_tools",
}


def normalize_role(value: str | None) -> str:
    role = (value or "").strip().lower()
    return role if role in ROLE_ORDER else "guest"


def role_sort_key(role: str) -> int:
    return ROLE_ORDER.get(role, -1)


def _password_is_set(value: str | None) -> bool:
    return bool((value or "").strip())


def _fetch_user(conn: sqlite3.Connection, *, user_id: int | None = None, username: str | None = None) -> dict[str, Any] | None:
    if not db_table_exists(conn, "app_users") or not db_table_exists(conn, "roles") or not db_table_exists(conn, "user_roles"):
        return None

    where_sql = "u.id = ?" if user_id is not None else "lower(u.username) = lower(?)"
    value = user_id if user_id is not None else username
    row = conn.execute(
        f"""
        SELECT
          u.id,
          u.username,
          u.display_name,
          u.password_hash,
          u.is_active,
          COALESCE(u.must_set_password, 0) AS must_set_password,
          COALESCE(u.is_builtin, 0) AS is_builtin,
          COALESCE(u.failed_login_attempts, 0) AS failed_login_attempts,
          COALESCE(u.locked_until, '') AS locked_until,
          COALESCE(u.last_login_at, '') AS last_login_at,
          COALESCE(GROUP_CONCAT(r.code, ','), '') AS role_codes
        FROM app_users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE {where_sql}
        GROUP BY u.id, u.username, u.display_name, u.password_hash, u.is_active, u.must_set_password, u.is_builtin, u.failed_login_attempts, u.locked_until, u.last_login_at
        LIMIT 1
        """,
        (value,),
    ).fetchone()
    if row is None:
        return None
    role_codes = [normalize_role(item) for item in str(row["role_codes"] or "").split(",") if item.strip()]
    role_codes = sorted(set(role_codes), key=role_sort_key)
    if not role_codes:
        role_codes = ["observer"]
    return {
        "id": int(row["id"]),
        "username": str(row["username"] or ""),
        "display_name": str(row["display_name"] or row["username"] or ""),
        "password_hash": str(row["password_hash"] or ""),
        "is_active": int(row["is_active"] or 0) == 1,
        "must_set_password": int(row["must_set_password"] or 0) == 1,
        "is_builtin": int(row["is_builtin"] or 0) == 1,
        "failed_login_attempts": int(row["failed_login_attempts"] or 0),
        "locked_until": str(row["locked_until"] or ""),
        "last_login_at": str(row["last_login_at"] or ""),
        "roles": role_codes,
    }


def _lookup_db_user(username: str) -> dict[str, Any] | None:
    try:
        conn = db_conn()
    except sqlite3.Error:
        return None
    try:
        return _fetch_user(conn, username=username)
    finally:
        conn.close()


def _session_user() -> dict[str, Any] | None:
    user_id = session.get("auth_user_id")
    if not user_id:
        return None
    try:
        conn = db_conn()
    except sqlite3.Error:
        return None
    try:
        user = _fetch_user(conn, user_id=int(user_id))
        if user is None or not user.get("is_active"):
            session.pop("auth_user_id", None)
            session.pop("auth_username", None)
            return None
        return user
    finally:
        conn.close()


def _derive_user_seed() -> tuple[str, list[str], bool, int | None]:
    session_user = _session_user()
    if session_user:
        return session_user["display_name"], list(session_user["roles"]), True, int(session_user["id"])

    if os.environ.get("ASTROMANAGER_AUTH_BYPASS", "0") == "1":
        env_username = (os.environ.get("ASTROMANAGER_AUTH_USERNAME") or os.environ.get("ASTROMANAGER_LOGIN_USER") or "").strip()
        env_role = normalize_role(os.environ.get("ASTROMANAGER_AUTH_ROLE") or os.environ.get("ASTROMANAGER_LOGIN_ROLE") or ("observer" if env_username else "guest"))
        if env_username:
            db_user = _lookup_db_user(env_username)
            if db_user and db_user.get("is_active"):
                return str(db_user["display_name"]), list(db_user["roles"]), True, int(db_user["id"])
            return env_username, [env_role], True, None

    return "Gast", ["guest"], False, None


def _permissions_for_roles(roles: list[str]) -> list[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(PERMISSIONS_BY_ROLE.get(role, set()))
    return sorted(permissions)


def build_auth_context() -> dict[str, Any]:
    display_name, roles, is_logged_in, user_id = _derive_user_seed()
    primary_role = sorted(roles, key=role_sort_key)[-1] if roles else "guest"
    permissions = _permissions_for_roles(roles)
    permission_set = set(permissions)

    return {
        "user_id": user_id,
        "is_logged_in": is_logged_in,
        "display_name": display_name,
        "username": display_name,
        "roles": roles,
        "roles_display": [ROLE_LABELS.get(role, role.title()) for role in roles],
        "primary_role": primary_role,
        "primary_role_label": ROLE_LABELS.get(primary_role, primary_role.title()),
        "permissions": permissions,
        "permission_set": permission_set,
        "status_label": "Eingeloggt" if is_logged_in else "Nicht angemeldet",
        "action_label": "Profil" if is_logged_in else "Login",
        "action_href": "/login",
        "can_view_overview": "view_overview" in permission_set,
        "can_view_logs": "view_logs" in permission_set,
        "can_view_system_status": "view_system_status" in permission_set,
        "can_run_workflows": "run_workflows" in permission_set,
        "can_manage_settings": "manage_settings" in permission_set,
        "can_view_settings_info": "view_settings_info" in permission_set,
        "can_manage_users": "manage_users" in permission_set,
        "can_view_database": "view_database" in permission_set,
        "can_manage_dev_tools": "manage_dev_tools" in permission_set,
    }


def get_auth_context() -> dict[str, Any]:
    cached = getattr(g, "astromanager_auth_context", None)
    if cached is None:
        cached = build_auth_context()
        g.astromanager_auth_context = cached
    return cached


def has_permission(permission: str, context: dict[str, Any] | None = None) -> bool:
    auth = context or get_auth_context()
    return permission in set(auth.get("permissions") or [])


def require_permission(permission: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not has_permission(permission):
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def action_permission(action: str) -> str | None:
    return ACTION_PERMISSIONS.get(action)


def build_login_info(context: dict[str, Any] | None = None) -> dict[str, Any]:
    auth = context or get_auth_context()
    return {
        "is_logged_in": bool(auth.get("is_logged_in")),
        "user_label": str(auth.get("display_name") or "Gast"),
        "status_label": str(auth.get("status_label") or "Nicht angemeldet"),
        "action_label": str(auth.get("action_label") or "Login"),
        "action_href": str(auth.get("action_href") or "/login"),
        "role_label": str(auth.get("primary_role_label") or "Gast"),
        "roles_display": list(auth.get("roles_display") or []),
        "permissions": list(auth.get("permissions") or []),
    }


def issue_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf_token(value: str | None) -> bool:
    return bool(value) and value == session.get("csrf_token")


def _password_error(password: str, confirm: str) -> str | None:
    if password != confirm:
        return "Die beiden Passwörter stimmen nicht überein."
    if len(password) < 12:
        return "Das Passwort muss mindestens 12 Zeichen lang sein."
    if password.lower() == password or password.upper() == password:
        return "Das Passwort muss Groß- und Kleinbuchstaben enthalten."
    if not any(ch.isdigit() for ch in password):
        return "Das Passwort muss mindestens eine Zahl enthalten."
    return None


def admin_bootstrap_status() -> dict[str, Any]:
    try:
        conn = db_conn()
    except sqlite3.Error:
        return {"bootstrap_needed": False, "admin_username": "admin"}
    try:
        if not db_table_exists(conn, "app_users") or not db_table_exists(conn, "roles") or not db_table_exists(conn, "user_roles"):
            return {"bootstrap_needed": False, "admin_username": "admin"}
        admin_with_password = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM app_users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE r.code='admin' AND u.is_active=1 AND TRIM(COALESCE(u.password_hash,'')) <> ''
            """
        ).fetchone()
        count = int(admin_with_password[0] or 0)
        bootstrap_user = conn.execute(
            "SELECT username, display_name FROM app_users WHERE lower(username)='admin' LIMIT 1"
        ).fetchone()
        return {
            "bootstrap_needed": count == 0,
            "admin_username": str((bootstrap_user["username"] if bootstrap_user else "admin") or "admin"),
            "admin_display_name": str((bootstrap_user["display_name"] if bootstrap_user else "Administrator") or "Administrator"),
        }
    finally:
        conn.close()


def bootstrap_admin_password(password: str, confirm: str) -> tuple[bool, str]:
    error = _password_error(password, confirm)
    if error:
        return False, error
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}"
    try:
        user = _fetch_user(conn, username="admin")
        if user is None:
            return False, "Bootstrap-Adminkonto nicht gefunden."
        conn.execute(
            """
            UPDATE app_users
            SET password_hash=?, must_set_password=0, password_updated_at=datetime('now'), updated_at=datetime('now'), failed_login_attempts=0, locked_until=''
            WHERE id=?
            """,
            (generate_password_hash(password), user["id"]),
        )
        conn.commit()
        return True, "Admin-Passwort wurde gesetzt. Du kannst dich jetzt anmelden."
    finally:
        conn.close()


def authenticate_user(username: str, password: str, remote_addr: str = "") -> tuple[bool, str, dict[str, Any] | None]:
    username = username.strip()
    if not username or not password:
        return False, "Benutzername und Passwort sind erforderlich.", None
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}", None
    try:
        user = _fetch_user(conn, username=username)
        if user is None or not user.get("is_active"):
            return False, "Ungültiger Benutzername oder Passwort.", None
        if user.get("locked_until"):
            row = conn.execute("SELECT datetime('now') < datetime(?)", (user["locked_until"],)).fetchone()
            if row and int(row[0] or 0) == 1:
                return False, "Dieses Konto ist vorübergehend gesperrt. Bitte später erneut versuchen.", None
        if not _password_is_set(user.get("password_hash")):
            return False, "Für dieses Konto ist noch kein Passwort gesetzt.", None
        if not check_password_hash(user["password_hash"], password):
            attempts = int(user.get("failed_login_attempts") or 0) + 1
            locked_until = ""
            if attempts >= 5:
                locked_until = conn.execute("SELECT datetime('now', '+15 minutes')").fetchone()[0]
                attempts = 0
            conn.execute(
                "UPDATE app_users SET failed_login_attempts=?, locked_until=?, updated_at=datetime('now') WHERE id=?",
                (attempts, locked_until, user["id"]),
            )
            conn.commit()
            return False, "Ungültiger Benutzername oder Passwort.", None
        conn.execute(
            """
            UPDATE app_users
            SET failed_login_attempts=0, locked_until='', last_login_at=datetime('now'), last_login_ip=?, updated_at=datetime('now')
            WHERE id=?
            """,
            (remote_addr or "", user["id"]),
        )
        conn.commit()
        user = _fetch_user(conn, user_id=user["id"])
        return True, "Login erfolgreich.", user
    finally:
        conn.close()


def login_user_session(user: dict[str, Any]) -> None:
    session.clear()
    session.permanent = True
    session["auth_user_id"] = int(user["id"])
    session["auth_username"] = str(user["username"])
    session["csrf_token"] = secrets.token_urlsafe(32)


def logout_user_session() -> None:
    session.clear()


def list_manageable_users() -> list[dict[str, Any]]:
    try:
        conn = db_conn()
    except sqlite3.Error:
        return []
    try:
        if not db_table_exists(conn, "app_users"):
            return []
        rows = conn.execute(
            """
            SELECT
              u.id, u.username, u.display_name, u.is_active, COALESCE(u.is_builtin,0) AS is_builtin, COALESCE(u.last_login_at,'') AS last_login_at,
              COALESCE(GROUP_CONCAT(r.code, ','), '') AS role_codes
            FROM app_users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            GROUP BY u.id, u.username, u.display_name, u.is_active, u.is_builtin, u.last_login_at
            ORDER BY lower(u.username) ASC
            """
        ).fetchall()
        items = []
        for row in rows:
            roles = [normalize_role(item) for item in str(row["role_codes"] or "").split(",") if item.strip()]
            roles = sorted(set(roles), key=role_sort_key) or ["observer"]
            primary_role = roles[-1]
            items.append({
                "id": int(row["id"]),
                "username": str(row["username"]),
                "display_name": str(row["display_name"]),
                "is_active": int(row["is_active"] or 0) == 1,
                "is_builtin": int(row["is_builtin"] or 0) == 1,
                "roles": roles,
                "primary_role": primary_role,
                "primary_role_label": ROLE_LABELS.get(primary_role, primary_role.title()),
                "last_login_at": str(row["last_login_at"] or ""),
            })
        return items
    finally:
        conn.close()


def create_user_by_admin(username: str, display_name: str, role: str, password: str, confirm: str, assigned_by: str) -> tuple[bool, str]:
    role = normalize_role(role)
    if role == "guest":
        return False, "Gast ist keine zuweisbare Benutzerrolle."
    username = username.strip().lower()
    display_name = display_name.strip() or username
    if not username or len(username) < 3:
        return False, "Der Benutzername muss mindestens 3 Zeichen lang sein."
    error = _password_error(password, confirm)
    if error:
        return False, error
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}"
    try:
        existing = _fetch_user(conn, username=username)
        if existing is not None:
            return False, "Dieser Benutzername existiert bereits."
        role_row = conn.execute("SELECT id FROM roles WHERE code=? LIMIT 1", (role,)).fetchone()
        if role_row is None:
            return False, "Die gewählte Rolle existiert nicht."
        cur = conn.execute(
            """
            INSERT INTO app_users (username, display_name, password_hash, is_active, note, must_set_password, is_builtin, created_at, updated_at, password_updated_at)
            VALUES (?, ?, ?, 1, '', 0, 0, datetime('now'), datetime('now'), datetime('now'))
            """,
            (username, display_name, generate_password_hash(password)),
        )
        user_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by) VALUES (?, ?, datetime('now'), ?)",
            (user_id, int(role_row[0]), assigned_by),
        )
        conn.commit()
        return True, f"Benutzer {username} wurde angelegt."
    finally:
        conn.close()


def admin_update_user_role(user_id: int, role: str, assigned_by: str) -> tuple[bool, str]:
    role = normalize_role(role)
    if role == "guest":
        return False, "Gast ist keine zuweisbare Benutzerrolle."
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}"
    try:
        user = _fetch_user(conn, user_id=user_id)
        if user is None:
            return False, "Benutzer nicht gefunden."
        role_row = conn.execute("SELECT id FROM roles WHERE code=? LIMIT 1", (role,)).fetchone()
        if role_row is None:
            return False, "Rolle nicht gefunden."
        conn.execute("DELETE FROM user_roles WHERE user_id=?", (user_id,))
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by) VALUES (?, ?, datetime('now'), ?)",
            (user_id, int(role_row[0]), assigned_by),
        )
        conn.execute("UPDATE app_users SET updated_at=datetime('now') WHERE id=?", (user_id,))
        conn.commit()
        return True, f"Rolle für {user['username']} aktualisiert."
    finally:
        conn.close()


def admin_set_user_password(user_id: int, password: str, confirm: str) -> tuple[bool, str]:
    error = _password_error(password, confirm)
    if error:
        return False, error
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}"
    try:
        user = _fetch_user(conn, user_id=user_id)
        if user is None:
            return False, "Benutzer nicht gefunden."
        conn.execute(
            "UPDATE app_users SET password_hash=?, must_set_password=0, failed_login_attempts=0, locked_until='', password_updated_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
            (generate_password_hash(password), user_id),
        )
        conn.commit()
        return True, f"Passwort für {user['username']} wurde gesetzt."
    finally:
        conn.close()


def admin_toggle_user_active(user_id: int, is_active: bool) -> tuple[bool, str]:
    try:
        conn = db_conn()
    except sqlite3.Error as exc:
        return False, f"Datenbankfehler: {exc}"
    try:
        user = _fetch_user(conn, user_id=user_id)
        if user is None:
            return False, "Benutzer nicht gefunden."
        if user['username'].lower() == 'admin' and not is_active:
            return False, 'Der Bootstrap-Admin kann nicht deaktiviert werden.'
        conn.execute("UPDATE app_users SET is_active=?, updated_at=datetime('now') WHERE id=?", (1 if is_active else 0, user_id))
        conn.commit()
        return True, f"Benutzer {user['username']} wurde {'aktiviert' if is_active else 'deaktiviert'}."
    finally:
        conn.close()


def build_login_page_data(context: dict[str, Any] | None = None, *, error: str = '', message: str = '') -> dict[str, Any]:
    auth = context or get_auth_context()
    bootstrap = admin_bootstrap_status()
    csrf_token = issue_csrf_token()
    return {
        'login_info': build_login_info(auth),
        'auth_context': auth,
        'csrf_token': csrf_token,
        'bootstrap_needed': bool(bootstrap.get('bootstrap_needed')),
        'bootstrap_admin_username': str(bootstrap.get('admin_username') or 'admin'),
        'bootstrap_admin_display_name': str(bootstrap.get('admin_display_name') or 'Administrator'),
        'error': error,
        'message': message,
        'manageable_users': list_manageable_users() if auth.get('can_manage_users') else [],
        'role_choices': [(code, ROLE_LABELS.get(code, code.title())) for code in ('observer', 'user', 'admin')],
    }
