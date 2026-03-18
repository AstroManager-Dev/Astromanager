from __future__ import annotations

import os
import sqlite3
from functools import wraps
from typing import Any, Callable

from flask import abort, g

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
        "view_gallery",
        "view_sessions",
        "view_targets",
        "view_atlas",
        "view_raw_files",
        "view_fits_viewer",
        "view_login",
    },
    "observer": {
        "view_gallery",
        "view_sessions",
        "view_targets",
        "view_atlas",
        "view_raw_files",
        "view_fits_viewer",
        "view_login",
    },
    "user": {
        "view_gallery",
        "view_sessions",
        "view_targets",
        "view_atlas",
        "view_raw_files",
        "view_fits_viewer",
        "view_login",
        "view_overview",
        "run_workflows",
        "view_system_status",
        "view_logs",
    },
    "admin": {
        "view_gallery",
        "view_sessions",
        "view_targets",
        "view_atlas",
        "view_raw_files",
        "view_fits_viewer",
        "view_login",
        "view_overview",
        "run_workflows",
        "view_system_status",
        "view_logs",
        "manage_settings",
        "manage_users",
        "view_database",
        "manage_dev_tools",
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


def _lookup_db_user(username: str) -> dict[str, Any] | None:
    try:
        conn = db_conn()
    except sqlite3.Error:
        return None

    try:
        if not db_table_exists(conn, "app_users") or not db_table_exists(conn, "roles") or not db_table_exists(conn, "user_roles"):
            return None

        row = conn.execute(
            """
            SELECT
              u.id,
              u.username,
              u.display_name,
              u.is_active,
              COALESCE(GROUP_CONCAT(r.code, ','), '') AS role_codes
            FROM app_users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            WHERE lower(u.username) = lower(?)
            GROUP BY u.id, u.username, u.display_name, u.is_active
            LIMIT 1
            """,
            (username,),
        ).fetchone()
        if row is None or int(row["is_active"] or 0) != 1:
            return None
        role_codes = [normalize_role(item) for item in str(row["role_codes"] or "").split(",") if item.strip()]
        role_codes = sorted(set(role_codes), key=role_sort_key)
        if not role_codes:
            role_codes = ["observer"]
        return {
            "username": str(row["username"] or username),
            "display_name": str(row["display_name"] or row["username"] or username),
            "roles": role_codes,
        }
    finally:
        conn.close()


def _derive_user_seed() -> tuple[str, list[str], bool]:
    env_username = (os.environ.get("ASTROMANAGER_AUTH_USERNAME") or os.environ.get("ASTROMANAGER_LOGIN_USER") or "").strip()
    env_role = normalize_role(os.environ.get("ASTROMANAGER_AUTH_ROLE") or os.environ.get("ASTROMANAGER_LOGIN_ROLE") or ("observer" if env_username else "guest"))
    if not env_username:
        return "Gast", ["guest"], False

    db_user = _lookup_db_user(env_username)
    if db_user:
        return str(db_user["display_name"]), list(db_user["roles"]), True

    return env_username, [env_role], True


def _permissions_for_roles(roles: list[str]) -> list[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(PERMISSIONS_BY_ROLE.get(role, set()))
    return sorted(permissions)


def build_auth_context() -> dict[str, Any]:
    display_name, roles, is_logged_in = _derive_user_seed()
    primary_role = sorted(roles, key=role_sort_key)[-1] if roles else "guest"
    permissions = _permissions_for_roles(roles)
    permission_set = set(permissions)
    action_href = (os.environ.get("ASTROMANAGER_LOGIN_HREF") or "/login").strip() or "/login"

    return {
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
        "action_href": action_href,
        "can_view_overview": "view_overview" in permission_set,
        "can_view_logs": "view_logs" in permission_set,
        "can_view_system_status": "view_system_status" in permission_set,
        "can_run_workflows": "run_workflows" in permission_set,
        "can_manage_settings": "manage_settings" in permission_set,
        "can_manage_users": "manage_users" in permission_set,
        "can_view_database": "view_database" in permission_set,
        "can_manage_dev_tools": "manage_dev_tools" in permission_set,
    }


class PermissionDenied(RuntimeError):
    pass


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
