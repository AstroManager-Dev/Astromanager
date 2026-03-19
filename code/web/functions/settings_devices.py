from __future__ import annotations

import re
from typing import Any

try:
    from astromanager.security.device_credentials import encrypt_device_password, mask_device_password
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, '/project-core/code/lib/py')
    from astromanager.security.device_credentials import encrypt_device_password, mask_device_password

from .database import db_conn, db_table_columns, db_table_exists, row_to_dict

ALLOWED_AUTH_MODES = {"anonymous", "login"}


def _slugify_instance_key(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug


def _build_unique_instance_key(conn: Any, seed: str, exclude_id: int | None = None) -> str:
    base = _slugify_instance_key(seed) or "device_instance"
    candidate = base
    suffix = 2
    while True:
        params = [candidate]
        sql = 'SELECT id FROM device_instances WHERE lower(instance_key) = lower(?)'
        if exclude_id is not None:
            sql += ' AND id <> ?'
            params.append(exclude_id)
        sql += ' LIMIT 1'
        row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            return candidate
        candidate = f"{base}_{suffix}"
        suffix += 1


def list_device_sources_settings() -> list[dict[str, Any]]:
    with db_conn() as conn:
        columns = set(db_table_columns(conn, 'device_sources'))
        remote_base_expr = "COALESCE(remote_base_dir, '/Astronomy')" if 'remote_base_dir' in columns else "'/Astronomy'"
        allowed_ext_expr = "COALESCE(allowed_extensions, '')" if 'allowed_extensions' in columns else "''"
        rows = conn.execute(
            f"""
            SELECT id, source_key, vendor, model, family, protocol, root_pattern,
                   {remote_base_expr} AS remote_base_dir,
                   {allowed_ext_expr} AS allowed_extensions,
                   notes, is_active
            FROM device_sources
            ORDER BY vendor, model, id
            """
        ).fetchall()
    return [row_to_dict(row) for row in rows]


def list_device_instances_settings() -> list[dict[str, Any]]:
    with db_conn() as conn:
        if not db_table_exists(conn, 'device_instances'):
            return []
        columns = set(db_table_columns(conn, 'device_instances'))
        remote_root_expr = "COALESCE(di.remote_base_dir_override, '')" if 'remote_base_dir_override' in columns else "''"
        allowed_ext_expr = "COALESCE(di.allowed_extensions_override, '')" if 'allowed_extensions_override' in columns else "''"
        notes_expr = "COALESCE(di.notes, '')" if 'notes' in columns else "''"
        password_expr = "COALESCE(di.password_enc, di.password_text, '')" if 'password_enc' in columns else "COALESCE(di.password_text, '')"
        rows = conn.execute(
            f"""
            SELECT di.id, di.instance_key, di.display_name, di.source_id, di.connection_kind, di.host, di.port,
                   di.auth_mode, di.username, di.timeout_seconds, di.is_active, di.is_default,
                   {remote_root_expr} AS remote_base_dir_override,
                   {allowed_ext_expr} AS allowed_extensions_override,
                   {notes_expr} AS notes,
                   {password_expr} AS password_secret,
                   ds.source_key, ds.vendor, ds.model, ds.remote_base_dir, ds.allowed_extensions
            FROM device_instances di
            JOIN device_sources ds ON ds.id = di.source_id
            ORDER BY di.is_default DESC, di.is_active DESC, di.display_name, di.id
            """
        ).fetchall()
    items = [row_to_dict(row) for row in rows]
    for item in items:
        item["password_masked"] = mask_device_password(item.get("password_secret"))
        item["effective_remote_base_dir"] = item.get("remote_base_dir_override") or item.get("remote_base_dir") or "/Astronomy"
        item["effective_allowed_extensions"] = item.get("allowed_extensions_override") or item.get("allowed_extensions") or ".fits,.fit,.fts"
        item["is_login"] = (item.get("auth_mode") or "anonymous") == "login"
    return items


def _normalize_bool(form_value: str | None) -> int:
    return 1 if str(form_value or '').strip() in {'1', 'true', 'on', 'yes'} else 0


def _normalize_int(form_value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(str(form_value or '').strip() or default)
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _clean_instance_payload(form: Any) -> dict[str, Any]:
    auth_mode = (form.get('auth_mode') or 'anonymous').strip().lower()
    if auth_mode not in ALLOWED_AUTH_MODES:
        auth_mode = 'anonymous'
    instance_key = _slugify_instance_key(form.get('instance_key') or '')
    display_name = (form.get('display_name') or '').strip()
    source_id = _normalize_int(form.get('source_id'), 0, 0, 10_000_000)
    port = _normalize_int(form.get('port'), 21, 1, 65535)
    timeout_seconds = _normalize_int(form.get('timeout_seconds'), 15, 1, 600)
    username = (form.get('username') or '').strip()
    password = (form.get('password') or '')
    if auth_mode == 'anonymous':
        username = 'anonymous'
        password = ''
    elif not username:
        raise ValueError('Für Login ist ein Benutzername erforderlich.')
    payload = {
        'instance_key': instance_key,
        'display_name': display_name,
        'source_id': source_id,
        'connection_kind': (form.get('connection_kind') or 'ftp').strip() or 'ftp',
        'host': (form.get('host') or '').strip(),
        'port': port,
        'auth_mode': auth_mode,
        'username': username,
        'password_enc': encrypt_device_password(password),
        'timeout_seconds': timeout_seconds,
        'remote_base_dir_override': (form.get('remote_base_dir_override') or '').strip(),
        'allowed_extensions_override': (form.get('allowed_extensions_override') or '').strip(),
        'notes': (form.get('notes') or '').strip(),
        'is_active': _normalize_bool(form.get('is_active')),
        'is_default': _normalize_bool(form.get('is_default')),
    }
    if not payload['display_name']:
        raise ValueError('Anzeigename fehlt.')
    if payload['source_id'] <= 0:
        raise ValueError('Source-Auswahl fehlt.')
    if not payload['host']:
        raise ValueError('Host oder IP fehlt.')
    if payload['is_default'] and not payload['is_active']:
        payload['is_active'] = 1
    return payload


def _ensure_default_instance(conn: Any) -> None:
    row = conn.execute(
        "SELECT id FROM device_instances WHERE COALESCE(is_active, 0) = 1 ORDER BY COALESCE(is_default, 0) DESC, id LIMIT 1"
    ).fetchone()
    if row is None:
        return
    conn.execute("UPDATE device_instances SET is_default = 0 WHERE COALESCE(is_default, 0) = 1")
    conn.execute("UPDATE device_instances SET is_default = 1 WHERE id = ?", (int(row['id']),))


def create_device_instance(form: Any) -> tuple[bool, str]:
    try:
        payload = _clean_instance_payload(form)
    except ValueError as exc:
        return False, str(exc)
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'device_instances'):
            return False, 'Device-Instances-Tabelle fehlt.'
        source = conn.execute('SELECT id FROM device_sources WHERE id = ? LIMIT 1', (payload['source_id'],)).fetchone()
        if source is None:
            return False, 'Gewählte Source existiert nicht.'
        payload['instance_key'] = _build_unique_instance_key(conn, payload['instance_key'] or payload['display_name'])
        if payload['is_default']:
            conn.execute("UPDATE device_instances SET is_default = 0 WHERE COALESCE(is_default, 0) = 1")
        conn.execute(
            """
            INSERT INTO device_instances(
              instance_key, display_name, source_id, connection_kind, host, port,
              auth_mode, username, password_enc, timeout_seconds,
              remote_base_dir_override, allowed_extensions_override, notes,
              is_active, is_default, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                payload['instance_key'], payload['display_name'], payload['source_id'], payload['connection_kind'], payload['host'], payload['port'],
                payload['auth_mode'], payload['username'], payload['password_enc'], payload['timeout_seconds'],
                payload['remote_base_dir_override'], payload['allowed_extensions_override'], payload['notes'],
                payload['is_active'], payload['is_default'],
            ),
        )
        if conn.execute("SELECT COUNT(*) AS n FROM device_instances WHERE COALESCE(is_default, 0) = 1").fetchone()['n'] == 0:
            _ensure_default_instance(conn)
        conn.commit()
        return True, f"Geräteinstanz „{payload['display_name']}“ gespeichert."
    finally:
        conn.close()


def update_device_instance(instance_id: int, form: Any) -> tuple[bool, str]:
    try:
        payload = _clean_instance_payload(form)
    except ValueError as exc:
        return False, str(exc)
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'device_instances'):
            return False, 'Device-Instances-Tabelle fehlt.'
        existing = conn.execute('SELECT id, display_name, instance_key, password_enc, password_text FROM device_instances WHERE id = ? LIMIT 1', (instance_id,)).fetchone()
        if existing is None:
            return False, 'Geräteinstanz nicht gefunden.'
        source = conn.execute('SELECT id FROM device_sources WHERE id = ? LIMIT 1', (payload['source_id'],)).fetchone()
        if source is None:
            return False, 'Gewählte Source existiert nicht.'
        payload['instance_key'] = _build_unique_instance_key(conn, payload['instance_key'] or existing['instance_key'], exclude_id=instance_id)
        password_enc = payload['password_enc']
        if not password_enc:
            password_enc = existing['password_enc'] if 'password_enc' in existing.keys() else ''
            if not password_enc:
                password_enc = existing['password_text'] if 'password_text' in existing.keys() else ''
        if payload['is_default']:
            conn.execute('UPDATE device_instances SET is_default = 0 WHERE COALESCE(is_default, 0) = 1 AND id <> ?', (instance_id,))
        conn.execute(
            """
            UPDATE device_instances
            SET instance_key = ?,
                display_name = ?,
                source_id = ?,
                connection_kind = ?,
                host = ?,
                port = ?,
                auth_mode = ?,
                username = ?,
                password_enc = ?,
                timeout_seconds = ?,
                remote_base_dir_override = ?,
                allowed_extensions_override = ?,
                notes = ?,
                is_active = ?,
                is_default = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                payload['instance_key'], payload['display_name'], payload['source_id'], payload['connection_kind'], payload['host'], payload['port'],
                payload['auth_mode'], payload['username'], password_enc, payload['timeout_seconds'],
                payload['remote_base_dir_override'], payload['allowed_extensions_override'], payload['notes'],
                payload['is_active'], payload['is_default'], instance_id,
            ),
        )
        if conn.execute("SELECT COUNT(*) AS n FROM device_instances WHERE COALESCE(is_default, 0) = 1").fetchone()['n'] == 0:
            _ensure_default_instance(conn)
        conn.commit()
        return True, f"Geräteinstanz „{payload['display_name']}“ aktualisiert."
    finally:
        conn.close()


def delete_device_instance(instance_id: int) -> tuple[bool, str]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'device_instances'):
            return False, 'Device-Instances-Tabelle fehlt.'
        row = conn.execute('SELECT id, display_name, COALESCE(is_default, 0) AS is_default FROM device_instances WHERE id = ? LIMIT 1', (instance_id,)).fetchone()
        if row is None:
            return False, 'Geräteinstanz nicht gefunden.'
        conn.execute('DELETE FROM device_instances WHERE id = ?', (instance_id,))
        if int(row['is_default'] or 0) == 1:
            _ensure_default_instance(conn)
        conn.commit()
        return True, f'Geräteinstanz „{row["display_name"]}“ gelöscht.'
    finally:
        conn.close()
