from __future__ import annotations

from typing import Any

from .database import db_conn, db_table_exists, row_to_dict


def _normalize_timezone_name(value: str | None) -> str:
    return str(value or '').strip()


def list_observing_sites() -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return []
        rows = conn.execute(
            """
            SELECT
                os.*,
                (SELECT COUNT(*) FROM sessions s WHERE COALESCE(s.observing_site_id, 0) = os.id) AS session_count
            FROM observing_sites os
            ORDER BY COALESCE(os.is_default, 0) DESC, lower(os.name), os.id
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def load_observing_site(site_id: int) -> dict[str, Any] | None:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return None
        row = conn.execute('SELECT * FROM observing_sites WHERE id = ? LIMIT 1', (site_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def load_default_observing_site() -> dict[str, Any] | None:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return None
        row = conn.execute('SELECT * FROM observing_sites WHERE COALESCE(is_default, 0) = 1 ORDER BY id LIMIT 1').fetchone()
        if row is None:
            row = conn.execute('SELECT * FROM observing_sites ORDER BY id LIMIT 1').fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def create_observing_site(name: str, latitude_deg: float, longitude_deg: float, elevation_m: float | None, timezone_name: str, set_default: bool = False) -> tuple[bool, str]:
    clean_name = str(name or '').strip()
    if not clean_name:
        return False, 'Standortname fehlt.'
    if latitude_deg < -90 or latitude_deg > 90:
        return False, 'Breitengrad muss zwischen -90 und 90 liegen.'
    if longitude_deg < -180 or longitude_deg > 180:
        return False, 'Längengrad muss zwischen -180 und 180 liegen.'
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return False, 'Standorttabelle fehlt.'
        exists = conn.execute('SELECT id FROM observing_sites WHERE lower(name) = lower(?) LIMIT 1', (clean_name,)).fetchone()
        if exists is not None:
            return False, 'Ein Standort mit diesem Namen existiert bereits.'
        current_default = conn.execute('SELECT COUNT(*) AS n FROM observing_sites WHERE COALESCE(is_default, 0) = 1').fetchone()['n']
        target_default = 1 if set_default or int(current_default or 0) == 0 else 0
        if target_default:
            conn.execute("UPDATE observing_sites SET is_default = 0, updated_at = datetime('now') WHERE COALESCE(is_default, 0) = 1")
        conn.execute(
            """
            INSERT INTO observing_sites(name, latitude_deg, longitude_deg, elevation_m, timezone_name, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (clean_name, latitude_deg, longitude_deg, elevation_m, _normalize_timezone_name(timezone_name), target_default),
        )
        conn.commit()
        return True, f'Standort „{clean_name}“ gespeichert.'
    finally:
        conn.close()


def set_default_observing_site(site_id: int) -> tuple[bool, str]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return False, 'Standorttabelle fehlt.'
        row = conn.execute('SELECT id, name FROM observing_sites WHERE id = ? LIMIT 1', (site_id,)).fetchone()
        if row is None:
            return False, 'Standort nicht gefunden.'
        conn.execute("UPDATE observing_sites SET is_default = 0, updated_at = datetime('now') WHERE COALESCE(is_default, 0) = 1")
        conn.execute("UPDATE observing_sites SET is_default = 1, updated_at = datetime('now') WHERE id = ?", (site_id,))
        conn.commit()
        return True, f'Standard-Standort ist jetzt „{row["name"]}“.'
    finally:
        conn.close()


def delete_observing_site(site_id: int) -> tuple[bool, str]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'observing_sites'):
            return False, 'Standorttabelle fehlt.'
        row = conn.execute('SELECT id, name, COALESCE(is_default, 0) AS is_default FROM observing_sites WHERE id = ? LIMIT 1', (site_id,)).fetchone()
        if row is None:
            return False, 'Standort nicht gefunden.'
        usage = conn.execute('SELECT COUNT(*) AS n FROM sessions WHERE COALESCE(observing_site_id, 0) = ?', (site_id,)).fetchone()['n']
        if int(usage or 0) > 0:
            return False, 'Standort ist noch Sessions zugeordnet und kann nicht gelöscht werden.'
        conn.execute('DELETE FROM observing_sites WHERE id = ?', (site_id,))
        if int(row['is_default'] or 0) == 1:
            next_row = conn.execute('SELECT id FROM observing_sites ORDER BY id LIMIT 1').fetchone()
            if next_row is not None:
                conn.execute("UPDATE observing_sites SET is_default = 1, updated_at = datetime('now') WHERE id = ?", (next_row['id'],))
        conn.commit()
        return True, f'Standort „{row["name"]}“ gelöscht.'
    finally:
        conn.close()


def assign_session_observing_site(session_id: int, site_id: int | None) -> tuple[bool, str]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, 'sessions'):
            return False, 'Session-Tabelle fehlt.'
        session_row = conn.execute('SELECT id FROM sessions WHERE id = ? LIMIT 1', (session_id,)).fetchone()
        if session_row is None:
            return False, 'Session nicht gefunden.'
        target_site_id = None
        if site_id is not None:
            if not db_table_exists(conn, 'observing_sites'):
                return False, 'Standorttabelle fehlt.'
            site_row = conn.execute('SELECT id, name FROM observing_sites WHERE id = ? LIMIT 1', (site_id,)).fetchone()
            if site_row is None:
                return False, 'Standort nicht gefunden.'
            target_site_id = int(site_row['id'])
            site_name = str(site_row['name'])
        else:
            site_name = ''
        conn.execute('UPDATE sessions SET observing_site_id = ? WHERE id = ?', (target_site_id, session_id))
        if db_table_exists(conn, 'session_moon_ephemeris'):
            conn.execute('DELETE FROM session_moon_ephemeris WHERE session_id = ?', (session_id,))
        if db_table_exists(conn, 'session_sun_ephemeris'):
            conn.execute('DELETE FROM session_sun_ephemeris WHERE session_id = ?', (session_id,))
        conn.commit()
        if target_site_id is None:
            return True, 'Session-Standort entfernt. Falls vorhanden wird der Standard-Standort verwendet.'
        return True, f'Session verwendet jetzt den Standort „{site_name}“.'
    finally:
        conn.close()
