#!/usr/bin/env python3
import math
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request, send_file

from actions import ACTION_HANDLERS
from progress_runtime import get_live_progress

APP = Flask(__name__)

LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))
LOG_FILE = LOG_ROOT / "master" / "webui.log"
DB_PATH = Path(os.environ.get("DB_PATH", "/runtime/pipeline.db"))
ASTROCTL = "/app/bin/astroctl"
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/app"))
CORE_BACKUP_ROOT = Path(os.environ.get("CORE_BACKUP_ROOT", "/runtime/backups/core"))
SQL_DUMP_ROOT = Path(os.environ.get("SQL_DUMP_ROOT", "/runtime/backups/sql"))
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", "/runtime/uploads"))
PROJECT_CORE_ROOT = Path(os.environ.get("PROJECT_CORE_ROOT", "/project-core"))

DB_TABLE_DEFAULTS = {
    "sessions": {
        "default_sort": "id",
        "search_columns": ["raw_session_path", "target", "category", "status", "filter_set", "session_type"],
    },
    "targets": {
        "default_sort": "id",
        "search_columns": ["canonical_name", "display_name", "category", "final_name"],
    },
    "capture_profiles": {
        "default_sort": "id",
        "search_columns": ["camera", "filter_set"],
    },
    "calibration_assets": {
        "default_sort": "id",
        "search_columns": ["asset_type", "asset_origin", "camera", "abs_path", "rel_path"],
    },
    "raw_files": {
        "default_sort": "id",
        "search_columns": [
            "file_name", "abs_path", "rel_path", "source_domain", "source_subtype",
            "filter_set", "file_status", "derivative_kind", "header_object",
            "header_bayerpat", "header_date_obs",
        ],
    },
}


TARGET_THUMBNAIL_FILE_NAME = "stacked_thumbnail.jpg"
TARGET_THUMB_CENTER_RADIUS_FACTOR = 0.05


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _is_system_target(item: dict[str, Any]) -> bool:
    category = str(item.get("category") or "").strip().lower()
    return category in {"sun", "moon"}


def _angular_sep_deg(ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float) -> float:
    ra1 = math.radians(ra1_deg)
    dec1 = math.radians(dec1_deg)
    ra2 = math.radians(ra2_deg)
    dec2 = math.radians(dec2_deg)
    cos_sep = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


def _session_center_radius_deg(row: dict[str, Any]) -> float | None:
    fov_x = _num(row.get("solve_fov_x_deg"))
    fov_y = _num(row.get("solve_fov_y_deg"))
    if fov_x is None or fov_y is None:
        return None
    if fov_x <= 0 or fov_y <= 0:
        return None
    return min(fov_x, fov_y) * TARGET_THUMB_CENTER_RADIUS_FACTOR


def _target_center_sep_deg(row: dict[str, Any], target: dict[str, Any]) -> float | None:
    distance = _num(row.get("distance_to_center_deg"))
    if distance is not None:
        return distance

    solve_ra = _num(row.get("solve_ra_deg"))
    solve_dec = _num(row.get("solve_dec_deg"))
    target_ra = _num(target.get("final_ra_deg"))
    target_dec = _num(target.get("final_dec_deg"))
    if None in (solve_ra, solve_dec, target_ra, target_dec):
        return None
    return _angular_sep_deg(float(solve_ra), float(solve_dec), float(target_ra), float(target_dec))


def _pick_target_thumbnail(conn: sqlite3.Connection, target: dict[str, Any]) -> dict[str, Any] | None:
    if not db_table_exists(conn, "sessions") or not db_table_exists(conn, "raw_files"):
        return None

    raw_columns = set(db_table_columns(conn, "raw_files"))
    session_columns = set(db_table_columns(conn, "sessions"))
    has_session_targets = db_table_exists(conn, "session_targets")

    if "session_key" not in raw_columns or "file_name" not in raw_columns or "abs_path" not in raw_columns:
        return None
    if "session_key" not in session_columns:
        return None

    target_id = int(target.get("id") or 0)
    if target_id <= 0:
        return None

    raw_current_sql = " AND COALESCE(rf.is_current, 1) = 1" if "is_current" in raw_columns else ""
    select_parts = [
        "rf.id AS raw_file_id",
        "rf.abs_path",
        "s.id AS session_id",
        "s.session_datetime" if "session_datetime" in session_columns else "NULL AS session_datetime",
        "s.target_id AS session_target_id" if "target_id" in session_columns else "NULL AS session_target_id",
        "s.solve_ra_deg" if "solve_ra_deg" in session_columns else "NULL AS solve_ra_deg",
        "s.solve_dec_deg" if "solve_dec_deg" in session_columns else "NULL AS solve_dec_deg",
        "s.solve_fov_x_deg" if "solve_fov_x_deg" in session_columns else "NULL AS solve_fov_x_deg",
        "s.solve_fov_y_deg" if "solve_fov_y_deg" in session_columns else "NULL AS solve_fov_y_deg",
    ]
    joins: list[str] = []
    params: list[Any] = [TARGET_THUMBNAIL_FILE_NAME]
    where_parts: list[str] = []

    if "target_id" in session_columns:
        where_parts.append("s.target_id = ?")
        params.append(target_id)

    if has_session_targets:
        st_columns = set(db_table_columns(conn, "session_targets"))
        joins.append("LEFT JOIN session_targets st ON st.session_id = s.id AND st.target_id = ?")
        params.append(target_id)
        where_parts.append("st.target_id = ?")
        params.append(target_id)
        select_parts.extend([
            "st.distance_to_center_deg" if "distance_to_center_deg" in st_columns else "NULL AS distance_to_center_deg",
            "st.is_primary" if "is_primary" in st_columns else "0 AS is_primary",
            "st.is_requested_target" if "is_requested_target" in st_columns else "0 AS is_requested_target",
        ])
    else:
        select_parts.extend([
            "NULL AS distance_to_center_deg",
            "0 AS is_primary",
            "0 AS is_requested_target",
        ])

    if not where_parts:
        return None

    rows = conn.execute(
        f"""
        SELECT DISTINCT
            {', '.join(select_parts)}
        FROM sessions s
        JOIN raw_files rf
          ON rf.session_key = s.session_key
         AND rf.file_name = ?
         {raw_current_sql}
        {' '.join(joins)}
        WHERE {' OR '.join(where_parts)}
        ORDER BY COALESCE(s.session_datetime, '') DESC, s.id DESC, rf.id DESC
        """,
        params,
    ).fetchall()

    best: dict[str, Any] | None = None
    best_key: tuple[int, str, int, int] | None = None
    is_system = _is_system_target(target)

    for row in rows:
        item = row_to_dict(row)
        session_target_id = int(item.get("session_target_id") or 0)
        is_direct = session_target_id == target_id
        is_primary = bool(item.get("is_primary"))
        is_requested = bool(item.get("is_requested_target"))
        center_sep = _target_center_sep_deg(item, target)
        center_radius = _session_center_radius_deg(item)
        within_center = (
            center_sep is not None
            and center_radius is not None
            and center_sep <= center_radius
        )

        accepted = True if is_system else (is_direct or is_requested or is_primary or within_center)
        if not accepted:
            continue

        score = 0
        if is_direct:
            score += 400
        if is_requested:
            score += 300
        if is_primary:
            score += 200
        if within_center:
            score += 100
        if center_sep is not None:
            score += max(0, int((1.0 - min(center_sep, 1.0)) * 100))

        session_dt = str(item.get("session_datetime") or "")
        sort_key = (score, session_dt, int(item.get("session_id") or 0), int(item.get("raw_file_id") or 0))
        if best_key is None or sort_key > best_key:
            best_key = sort_key
            best = item
            best["thumb_center_sep_deg"] = center_sep
            best["thumb_center_radius_deg"] = center_radius

    return best


def _apply_target_thumb(conn: sqlite3.Connection, target: dict[str, Any]) -> None:
    thumb = _pick_target_thumbnail(conn, target)
    if thumb:
        target["thumb_url"] = f"/media/raw-file/{int(thumb['raw_file_id'])}"
        target["thumb_href"] = ""
        target["thumb_source"] = "session"
        target["thumb_session_id"] = int(thumb.get("session_id") or 0)
        target["thumb_session_datetime"] = str(thumb.get("session_datetime") or "")
        target["thumb_center_sep_deg"] = thumb.get("thumb_center_sep_deg")
        target["thumb_center_radius_deg"] = thumb.get("thumb_center_radius_deg")
        return

    legacy_url = str(target.get("legacy_image_url") or "")
    legacy_status = str(target.get("legacy_status") or "").lower()
    if legacy_url and legacy_status == "resolved":
        target["thumb_url"] = legacy_url
        target["thumb_href"] = str(target.get("legacy_viewer_url") or target.get("legacy_fits_url") or "")
        target["thumb_source"] = "legacy"
        return

    skyview_url = str(target.get("skyview_image_url") or "")
    skyview_status = str(target.get("skyview_status") or "").lower()
    if skyview_url and skyview_status == "resolved":
        target["thumb_url"] = skyview_url
        target["thumb_href"] = str(target.get("skyview_fits_url") or "")
        target["thumb_source"] = "skyview"
        return

    target["thumb_url"] = str(target.get("nasa_thumb_url") or "")
    target["thumb_href"] = str(target.get("nasa_page_url") or "") if target.get("nasa_thumb_url") else ""
    target["thumb_source"] = "nasa" if target.get("nasa_thumb_url") else ""



def _format_session_datetime_label(value: Any) -> str:
    raw = str(value or '').strip()
    if not raw:
        return '—'
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})[- T](\d{2})-(\d{2})(?:-(\d{2}))?', raw)
    if match:
        year, month, day, hour, minute, _second = match.groups()
        return f'{day}.{month}.{year} · {hour}:{minute}'
    return raw


def _format_session_group_label(value: str) -> str:
    raw = str(value or '').strip()
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', raw)
    if match:
        year, month, day = match.groups()
        return f'{day}.{month}.{year}'
    return raw or 'Unbekannt'


def _format_exposure_duration_label(total_seconds: Any) -> str:
    try:
        seconds = int(round(float(total_seconds or 0)))
    except Exception:
        return '—'
    if seconds <= 0:
        return '—'
    total_minutes = max(1, int(round(seconds / 60.0)))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours:
        return f'{hours}h {minutes:02d}m'
    return f'{total_minutes}m'


def app_version_value() -> str:
    try:
        return (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        return ""


@APP.context_processor
def inject_global_ui_context() -> dict[str, Any]:
    return {
        "app_version": app_version_value(),
    }


def latest_web_log(limit: int = 40) -> str:
    if not LOG_FILE.exists():
        return ""
    try:
        return "".join(LOG_FILE.read_text(encoding="utf-8").splitlines(keepends=True)[-limit:])
    except Exception:
        return ""


def running_jobs() -> list[dict[str, Any]]:
    return [run for run in db_recent_runs() if str(run.get("status", "")).lower() in {"running", "started"}]


def summarize_service_state() -> dict[str, Any]:
    progress = get_live_progress()
    active_runs = running_jobs()
    current_job = active_runs[0] if active_runs else None
    title = "Bereit"
    subtitle = "Kein aktiver Job"
    if progress.get("active"):
        title = "Lauf aktiv"
        subtitle = progress.get("status") or "AstroManager arbeitet"
    elif current_job:
        title = current_job.get("job_name") or "Letzter Job"
        subtitle = current_job.get("status") or "running"
    elif progress.get("status"):
        subtitle = progress.get("status")

    return {
        "title": title,
        "subtitle": subtitle,
        "active": bool(progress.get("active")),
        "workflow": progress.get("workflow") or "idle",
        "current_step": progress.get("current_step") or "",
        "progress_pct": progress.get("progress_pct") or 0,
        "current_job": current_job,
        "active_runs": active_runs,
        "recent_runs": db_recent_runs(),
        "latest_log": latest_web_log(),
    }


def file_cards_from_dir(path: Path, label: str, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for fp in sorted([p for p in path.glob('*') if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        stat = fp.stat()
        items.append({
            "name": fp.name,
            "label": label,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        })
    return items


def fmt_size(num: int) -> str:
    value = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num} B"


def dev_assets() -> dict[str, list[dict[str, Any]]]:
    backups = file_cards_from_dir(CORE_BACKUP_ROOT, "Core Backup", limit=50)
    sql_dumps = file_cards_from_dir(SQL_DUMP_ROOT, "SQL", limit=50)
    for bucket in (backups, sql_dumps):
        for item in bucket:
            item["size_label"] = fmt_size(int(item["size"]))
    latest_backup = backups[0] if backups else None
    return {"backups": backups, "sql_dumps": sql_dumps, "latest_backup": latest_backup}


def resolve_download(bucket: str, filename: str) -> Path:
    roots = {"backup": CORE_BACKUP_ROOT, "sql": SQL_DUMP_ROOT}
    if bucket not in roots:
        raise FileNotFoundError(bucket)
    safe_name = Path(filename).name
    target = (roots[bucket] / safe_name).resolve()
    root = roots[bucket].resolve()
    if root not in target.parents and target != root:
        raise FileNotFoundError(filename)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(filename)
    return target

def append_web_log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def db_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def db_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def db_table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(r["name"]) for r in rows]


def db_all_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name COLLATE NOCASE ASC
        """
    ).fetchall()
    return [str(r["name"]) for r in rows]


def build_table_config(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    cfg: dict[str, dict[str, Any]] = {}
    for table in db_all_tables(conn):
        columns = db_table_columns(conn, table)
        default_cfg = DB_TABLE_DEFAULTS.get(table, {})
        default_sort = default_cfg.get("default_sort", "id")
        if default_sort not in columns:
            default_sort = "id" if "id" in columns else (columns[0] if columns else "id")
        search_columns = [c for c in default_cfg.get("search_columns", []) if c in columns]
        if not search_columns:
            search_columns = columns[:]
        cfg[table] = {
            "default_sort": default_sort,
            "search_columns": search_columns,
        }
    return cfg


def parse_int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def parse_text_arg(name: str, default: str = "") -> str:
    return request.args.get(name, default).strip()


def dedupe_runs(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in rows:
        item = dict(row)
        key = (
            str(item.get("job_name", "")),
            str(item.get("started_at", "")),
            str(item.get("status", "")),
        )

        current = grouped.get(key)
        if current is None:
            grouped[key] = item
            continue

        current_source = str(current.get("source", ""))
        new_source = str(item.get("source", ""))

        def source_rank(value: str) -> int:
            if value == "workflow":
                return 3
            if value == "astroctl":
                return 2
            if value == "web":
                return 2
            return 1

        if source_rank(new_source) > source_rank(current_source):
            grouped[key] = item
            continue

        current_note = str(current.get("note", "") or "")
        new_note = str(item.get("note", "") or "")
        if len(new_note) > len(current_note):
            current["note"] = new_note

    deduped = list(grouped.values())
    deduped.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
    return deduped[:15]


def db_recent_runs() -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, job_name, status, started_at, finished_at, source, note
            FROM job_runs
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()
        return dedupe_runs(rows)
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def db_tables_summary() -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        table_cfg = build_table_config(conn)
        items: list[dict[str, Any]] = []
        for table in table_cfg:
            exists = db_table_exists(conn, table)
            columns = db_table_columns(conn, table) if exists else []
            count = None
            if exists:
                try:
                    count = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                except sqlite3.OperationalError:
                    count = None
            items.append(
                {
                    "name": table,
                    "exists": exists,
                    "columns": columns,
                    "default_sort": table_cfg[table]["default_sort"],
                    "search_columns": table_cfg[table]["search_columns"],
                    "row_count": count,
                }
            )
        return items
    finally:
        conn.close()



def _preferred_target_name(item: dict[str, Any]) -> str:
    for value in (
        item.get("label_de"),
        item.get("display_name"),
        item.get("final_name"),
        item.get("canonical_name"),
        item.get("label_en"),
    ):
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _catalog_target_name(item: dict[str, Any]) -> str:
    for value in (
        item.get("display_name"),
        item.get("final_name"),
        item.get("canonical_name"),
        item.get("label_en"),
    ):
        text = str(value or "").strip()
        if text:
            return text
    return ""

def _load_target_cards(where_sql: str = "", params: tuple[Any, ...] = (), limit: int = 100) -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, "targets"):
            return []

        has_target_final = db_table_exists(conn, "target_final")
        has_session_targets = db_table_exists(conn, "session_targets")
        has_session_target_resolve_item = db_table_exists(conn, "session_target_resolve_item")

        sessions_join = ""
        if has_session_targets and db_table_exists(conn, "sessions"):
            sessions_join = _target_session_count_join()
        elif has_session_targets:
            sessions_join = """
            LEFT JOIN (
                SELECT target_id, COUNT(DISTINCT session_id) AS session_count
                FROM session_targets
                WHERE target_id IS NOT NULL
                GROUP BY target_id
            ) sc
              ON sc.target_id = t.id
            """
        elif has_session_target_resolve_item:
            sessions_join = """
            LEFT JOIN (
                SELECT target_id, COUNT(DISTINCT session_id) AS session_count
                FROM session_target_resolve_item
                WHERE target_id IS NOT NULL
                GROUP BY target_id
            ) sc
              ON sc.target_id = t.id
            """
        elif db_table_exists(conn, "sessions"):
            sessions_join = """
            LEFT JOIN (
                SELECT target_id, COUNT(DISTINCT id) AS session_count
                FROM sessions
                WHERE target_id IS NOT NULL
                GROUP BY target_id
            ) sc
              ON sc.target_id = t.id
            """
        has_target_legacy = db_table_exists(conn, "target_legacy_survey_resolve")
        legacy_join = ""
        legacy_select = ""
        if has_target_legacy:
            legacy_join = """
                LEFT JOIN target_legacy_survey_resolve tls
                  ON tls.target_id = t.id
            """
            legacy_select = """
                    tls.image_url AS legacy_image_url,
                    tls.fits_url AS legacy_fits_url,
                    tls.viewer_url AS legacy_viewer_url,
                    tls.layer AS legacy_layer,
                    tls.status AS legacy_status,
            """

        has_target_skyview = db_table_exists(conn, "target_skyview_resolve")
        skyview_join = ""
        skyview_select = ""
        if has_target_skyview:
            skyview_join = """
                LEFT JOIN target_skyview_resolve tsv
                  ON tsv.target_id = t.id
            """
            skyview_select = """
                    tsv.image_url AS skyview_image_url,
                    tsv.fits_url AS skyview_fits_url,
                    tsv.survey AS skyview_survey,
                    tsv.status AS skyview_status,
            """

        if has_target_final:
            where_clause = f"WHERE {where_sql}" if where_sql.strip() else ""
            rows = conn.execute(
                f"""
                SELECT
                    t.id,
                    t.canonical_name,
                    t.display_name,
                    t.slug,
                    t.category,
                    t.wikidata_id,
                    t.label_de,
                    t.label_en,
                    t.aliases_de,
                    t.aliases_en,
                    t.object_type_label_de,
                    t.object_type_label_en,
                    t.nasa_title,
                    t.nasa_page_url,
                    t.nasa_thumb_url,
                    {legacy_select}
                    {skyview_select}
                    tf.final_name,
                    tf.final_name_source,
                    tf.final_objtype,
                    tf.final_objtype_source,
                    tf.final_ra_deg,
                    tf.final_dec_deg,
                    tf.final_coord_source,
                    tf.final_distance_value,
                    tf.final_distance_unit,
                    tf.distance_ly,
                    tf.distance_source,
                    tf.distance_ref,
                    tf.mag_value,
                    tf.mag_band,
                    tf.mag_source,
                    tf.constellation_code,
                    tf.constellation_name,
                    tf.constellation_source,
                    tf.identity_method,
                    tf.identity_confidence,
                    tf.coord_match_sep_arcsec,
                    tf.angular_size_arcmin,
                    tf.final_source_summary,
                    tf.merge_status,
                    tf.merge_notes,
                    COALESCE(sc.session_count, 0) AS session_count
                FROM targets t
                LEFT JOIN target_final tf
                  ON tf.target_id = t.id
                {legacy_join}
                {skyview_join}
                {sessions_join}
                {where_clause}
                ORDER BY COALESCE(tf.final_name, t.display_name, t.canonical_name) COLLATE NOCASE ASC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        else:
            columns = set(db_table_columns(conn, "targets"))
            wanted = [
                "id",
                "canonical_name",
                "display_name",
                "slug",
                "category",
                "constellation",
                "final_name",
                "final_objtype",
                "final_ra_deg",
                "final_dec_deg",
                "final_distance_value",
                "final_distance_unit",
                "final_source_summary",
                "nasa_title",
                "nasa_page_url",
                "nasa_thumb_url",
                "legacy_image_url",
                "legacy_fits_url",
                "legacy_viewer_url",
                "legacy_layer",
                "legacy_status",
                "skyview_image_url",
                "skyview_fits_url",
                "skyview_survey",
                "skyview_status",
                "wikidata_id",
                "label_de",
                "label_en",
                "aliases_de",
                "aliases_en",
                "object_type_label_de",
                "object_type_label_en",
            ]
            existing = [c for c in wanted if c in columns]
            if not existing:
                return []

            sort_col = "final_name" if "final_name" in columns else ("canonical_name" if "canonical_name" in columns else "id")
            where_clause = f"WHERE {where_sql}" if where_sql.strip() else ""

            has_target_legacy = db_table_exists(conn, "target_legacy_survey_resolve")
            has_target_skyview = db_table_exists(conn, "target_skyview_resolve")
            extra_select = ""
            extra_join = ""
            if has_target_legacy:
                extra_select += ", tls.image_url AS legacy_image_url, tls.fits_url AS legacy_fits_url, tls.viewer_url AS legacy_viewer_url, tls.layer AS legacy_layer, tls.status AS legacy_status"
                extra_join += " LEFT JOIN target_legacy_survey_resolve tls ON tls.target_id = t.id"
            if has_target_skyview:
                extra_select += ", tsv.image_url AS skyview_image_url, tsv.fits_url AS skyview_fits_url, tsv.survey AS skyview_survey, tsv.status AS skyview_status"
                extra_join += " LEFT JOIN target_skyview_resolve tsv ON tsv.target_id = t.id"

            rows = conn.execute(
                f"""
                SELECT {", ".join("t." + c for c in existing)}{extra_select},
                       COALESCE(sc.session_count, 0) AS session_count
                FROM targets t
                {extra_join}
                {sessions_join}
                {where_clause}
                ORDER BY t.{sort_col} COLLATE NOCASE ASC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            d = row_to_dict(row)

            catalog_name = _catalog_target_name(d)
            preferred_name = _preferred_target_name(d) or catalog_name
            d["display_name"] = preferred_name
            d["detail_display_name"] = preferred_name
            d["catalog_name"] = catalog_name
            d["subtitle"] = (d.get("canonical_name") or "").strip()
            d["objtype"] = (
                d.get("object_type_label_de")
                or d.get("final_objtype")
                or d.get("objtype")
                or ""
            ).strip()

            ra = d.get("final_ra_deg")
            dec = d.get("final_dec_deg")
            d["final_ra_deg_fmt"] = f"{ra:.6f}" if isinstance(ra, (int, float)) else ""
            d["final_dec_deg_fmt"] = f"{dec:.6f}" if isinstance(dec, (int, float)) else ""

            dist = d.get("final_distance_value")
            unit = (d.get("final_distance_unit") or "").strip()
            if isinstance(dist, (int, float)):
                if abs(dist) >= 1000:
                    d["distance_fmt"] = f"{dist:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    d["distance_fmt"] = f"{dist:.1f}".replace(".", ",")
            else:
                d["distance_fmt"] = ""
            d["distance_label"] = f'{d["distance_fmt"]} {unit}'.strip() if d["distance_fmt"] else ""

            size = d.get("angular_size_arcmin")
            d["angular_size_arcmin_fmt"] = (
                f"{size:.1f}".replace(".", ",") if isinstance(size, (int, float)) else ""
            )

            d["session_count"] = int(d.get("session_count") or 0)

            source_summary = (d.get("final_source_summary") or "").strip()
            d["source_summary_readable"] = source_summary.replace(";", " · ")
            _apply_target_thumb(conn, d)

            items.append(d)
        return items
    finally:
        conn.close()


def _target_session_count_join() -> str:
    return """
    LEFT JOIN (
        SELECT target_id, COUNT(DISTINCT session_id) AS session_count
        FROM (
            SELECT st.target_id AS target_id, st.session_id AS session_id
            FROM session_targets st
            WHERE st.target_id IS NOT NULL

            UNION

            SELECT s.target_id AS target_id, s.id AS session_id
            FROM sessions s
            WHERE s.target_id IS NOT NULL
        ) mapped
        GROUP BY target_id
    ) sc
      ON sc.target_id = t.id
    """



def _load_target_detail(target_id: int) -> dict[str, Any] | None:
    conn = db_conn()
    try:
        cards = _load_target_cards("t.id = ?", (target_id,), limit=1)
        if not cards:
            return None
        target = cards[0]

        if not db_table_exists(conn, "sessions"):
            target["sessions"] = []
            target["session_groups"] = []
            return target

        session_columns = set(db_table_columns(conn, "sessions"))
        has_session_targets = db_table_exists(conn, "session_targets")
        has_raw_files = db_table_exists(conn, "raw_files")
        raw_columns = set(db_table_columns(conn, "raw_files")) if has_raw_files else set()

        select_parts = [
            "s.id",
            "s.session_key" if "session_key" in session_columns else "NULL AS session_key",
            "s.session_datetime" if "session_datetime" in session_columns else "NULL AS session_datetime",
            "s.raw_session_path" if "raw_session_path" in session_columns else "NULL AS raw_session_path",
            "s.target" if "target" in session_columns else "NULL AS target",
            "s.category" if "category" in session_columns else "NULL AS category",
            "s.filter_set" if "filter_set" in session_columns else "NULL AS filter_set",
            "s.frame_count" if "frame_count" in session_columns else "NULL AS frame_count",
            "s.status" if "status" in session_columns else "NULL AS status",
            "s.solve_status" if "solve_status" in session_columns else "NULL AS solve_status",
            "s.platesolve_status" if "platesolve_status" in session_columns else "NULL AS platesolve_status",
            "s.target_final" if "target_final" in session_columns else "NULL AS target_final",
            "s.target_id" if "target_id" in session_columns else "NULL AS target_id",
            "s.exp" if "exp" in session_columns else "NULL AS exp",
            "s.gain" if "gain" in session_columns else "NULL AS gain",
            "CASE WHEN s.target_id = ? THEN 1 ELSE 0 END AS is_direct_target" if "target_id" in session_columns else "0 AS is_direct_target",
        ]

        params: list[Any] = []
        if "target_id" in session_columns:
            params.append(target_id)

        joins: list[str] = []
        where_parts: list[str] = []

        if "target_id" in session_columns:
            where_parts.append("s.target_id = ?")
            params.append(target_id)

        if has_session_targets:
            joins.append(
                """
            LEFT JOIN session_targets st
              ON st.session_id = s.id
             AND st.target_id = ?
            """
            )
            params.append(target_id)
            where_parts.append("st.target_id = ?")
            params.append(target_id)

        if has_raw_files and "session_key" in raw_columns:
            light_checks: list[str] = []
            if "source_subtype" in raw_columns:
                light_checks.append("rf.source_subtype = 'light_raw_frame'")
            if "derivative_kind" in raw_columns:
                light_checks.append("rf.derivative_kind = 'light_raw_frame'")
            if not light_checks:
                light_checks.append("0")

            preview_checks: list[str] = []
            if "source_subtype" in raw_columns:
                preview_checks.append("rf.source_subtype = 'dwarf_preview'")
            if "derivative_kind" in raw_columns:
                preview_checks.append("rf.derivative_kind = 'dwarf_preview'")
            if "file_name" in raw_columns:
                preview_checks.append("lower(rf.file_name) IN ('stacked.jpg', 'stacked_thumbnail.jpg')")
            if not preview_checks:
                preview_checks.append("0")

            joins.append(
                f"""
            LEFT JOIN (
                SELECT
                    rf.session_key,
                    SUM(CASE WHEN {' OR '.join(light_checks)} THEN 1 ELSE 0 END) AS light_frame_count,
                    MAX(CASE WHEN {' OR '.join(preview_checks)} THEN rf.id ELSE NULL END) AS dwarf_preview_raw_file_id
                FROM raw_files rf
                GROUP BY rf.session_key
            ) rfc
              ON rfc.session_key = s.session_key
            """
            )
            select_parts.append("COALESCE(rfc.light_frame_count, 0) AS light_frame_count")
            select_parts.append("rfc.dwarf_preview_raw_file_id AS dwarf_preview_raw_file_id")
        else:
            select_parts.append("0 AS light_frame_count")
            select_parts.append("NULL AS dwarf_preview_raw_file_id")

        if not where_parts:
            target["sessions"] = []
            target["session_groups"] = []
            return target

        try:
            rows = conn.execute(
                f"""
                SELECT DISTINCT
                    {', '.join(select_parts)}
                FROM sessions s
                {' '.join(joins)}
                WHERE {' OR '.join(where_parts)}
                ORDER BY COALESCE(s.session_datetime, '') DESC, s.id DESC
                """,
                params,
            ).fetchall()
        except sqlite3.Error as exc:
            append_web_log(f"target-detail sessions failed for target_id={target_id}: {exc}")
            target["sessions"] = []
            target["session_groups"] = []
            target["detail_error"] = str(exc)
            return target

        sessions: list[dict[str, Any]] = []
        for row in rows:
            item = row_to_dict(row)
            dt_value = str(item.get("session_datetime") or "")
            date_raw = dt_value[:10] if len(dt_value) >= 10 else ""
            item["session_date"] = _format_session_group_label(date_raw)
            item["session_datetime_label"] = _format_session_datetime_label(dt_value)
            item["session_button_label"] = item["session_datetime_label"]
            item["is_direct_target"] = bool(item.get("is_direct_target"))

            light_frame_count = int(item.get("light_frame_count") or 0)
            frame_count = int(item.get("frame_count") or 0)
            effective_light_count = light_frame_count if light_frame_count > 0 else frame_count
            item["light_frame_count"] = effective_light_count

            exp_value = item.get("exp")
            try:
                exp_float = float(exp_value) if exp_value not in (None, "") else None
            except Exception:
                exp_float = None
            gain_value = item.get("gain")
            try:
                gain_label = str(int(float(gain_value))) if gain_value not in (None, "") else "—"
            except Exception:
                gain_label = str(gain_value or "—")

            item["exp_label"] = f"{exp_float:.0f}s" if exp_float is not None else "—"
            item["gain_label"] = gain_label
            total_seconds = effective_light_count * exp_float if (effective_light_count > 0 and exp_float is not None) else 0
            item["total_exposure_label"] = _format_exposure_duration_label(total_seconds)
            item["session_href"] = f"/?table=sessions&filter_id={int(item.get('id') or 0)}"

            preview_id = item.get("dwarf_preview_raw_file_id")
            item["dwarf_preview_url"] = f"/media/raw-file/{int(preview_id)}" if preview_id else ""
            sessions.append(item)

        grouped: list[dict[str, Any]] = []
        for item in sessions:
            session_date = item["session_date"]
            if not grouped or grouped[-1]["date"] != session_date:
                grouped.append({"date": session_date, "session_items": []})
            grouped[-1]["session_items"].append(item)

        target["sessions"] = sessions
        target["session_groups"] = grouped
        return target
    finally:
        conn.close()


def _format_session_month_label(value: str) -> str:
    raw = str(value or '').strip()
    match = re.match(r'^(\d{4})-(\d{2})$', raw)
    if not match:
        return raw or 'Unbekannt'
    year, month = match.groups()
    names = {
        '01': 'Januar', '02': 'Februar', '03': 'März', '04': 'April',
        '05': 'Mai', '06': 'Juni', '07': 'Juli', '08': 'August',
        '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Dezember',
    }
    return f"{names.get(month, month)} {year}"


def _load_gallery_sessions() -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, "sessions"):
            return []

        session_columns = set(db_table_columns(conn, "sessions"))
        has_targets = db_table_exists(conn, "targets")
        has_target_final = db_table_exists(conn, "target_final")
        has_session_targets = db_table_exists(conn, "session_targets")
        has_raw_files = db_table_exists(conn, "raw_files")

        select_parts = [
            "s.id",
            "s.session_key" if "session_key" in session_columns else "NULL AS session_key",
            "s.session_datetime" if "session_datetime" in session_columns else "NULL AS session_datetime",
            "s.target" if "target" in session_columns else "NULL AS target",
            "s.raw_session_path" if "raw_session_path" in session_columns else "NULL AS raw_session_path",
            "s.exp" if "exp" in session_columns else "NULL AS exp",
            "s.gain" if "gain" in session_columns else "NULL AS gain",
        ]
        joins: list[str] = []

        if "target_id" in session_columns and has_target_final:
            joins.append("LEFT JOIN target_final dtf ON dtf.target_id = s.target_id")
            select_parts.append("dtf.final_name AS direct_final_name")
        else:
            select_parts.append("NULL AS direct_final_name")

        if "target_id" in session_columns and has_targets:
            joins.append("LEFT JOIN targets dt ON dt.id = s.target_id")
            select_parts.extend([
                "dt.label_de AS direct_label_de",
                "dt.display_name AS direct_display_name",
                "dt.canonical_name AS direct_canonical_name",
            ])
        else:
            select_parts.extend([
                "NULL AS direct_label_de",
                "NULL AS direct_display_name",
                "NULL AS direct_canonical_name",
            ])

        if has_session_targets:
            joins.append("LEFT JOIN session_targets st ON st.session_id = s.id")
            if has_targets:
                joins.append("LEFT JOIN targets t ON t.id = st.target_id")
            if has_target_final:
                joins.append("LEFT JOIN target_final tf ON tf.target_id = st.target_id")
            target_name_expr_parts = []
            if has_targets:
                target_name_expr_parts.extend(["NULLIF(t.label_de,'')", "NULLIF(t.display_name,'')", "NULLIF(t.canonical_name,'')"])
            if has_target_final:
                target_name_expr_parts.append("NULLIF(tf.final_name,'')")
            target_name_expr_parts.append("NULLIF(st.target_name,'')")
            target_name_expr = "COALESCE(" + ", ".join(target_name_expr_parts) + ", 'Unbenanntes Target')"
            select_parts.append(f"GROUP_CONCAT(DISTINCT {target_name_expr}) AS session_target_names")
        else:
            select_parts.append("NULL AS session_target_names")

        if has_raw_files:
            raw_columns = set(db_table_columns(conn, "raw_files"))
            if "session_key" in raw_columns:
                preview_checks: list[str] = []
                if "source_subtype" in raw_columns:
                    preview_checks.append("rf.source_subtype = 'dwarf_preview'")
                if "derivative_kind" in raw_columns:
                    preview_checks.append("rf.derivative_kind = 'dwarf_preview'")
                if "file_name" in raw_columns:
                    preview_checks.append("lower(rf.file_name) IN ('stacked.jpg', 'stacked_thumbnail.jpg')")
                if preview_checks:
                    joins.append(
                        f"""
                        LEFT JOIN (
                            SELECT
                                rf.session_key,
                                MAX(CASE WHEN {' OR '.join(preview_checks)} THEN rf.id ELSE NULL END) AS dwarf_preview_raw_file_id
                            FROM raw_files rf
                            GROUP BY rf.session_key
                        ) rfp ON rfp.session_key = s.session_key
                        """
                    )
                    select_parts.append("rfp.dwarf_preview_raw_file_id")
                else:
                    select_parts.append("NULL AS dwarf_preview_raw_file_id")
            else:
                select_parts.append("NULL AS dwarf_preview_raw_file_id")
        else:
            select_parts.append("NULL AS dwarf_preview_raw_file_id")

        rows = conn.execute(
            f"""
            SELECT
                {', '.join(select_parts)}
            FROM sessions s
            {' '.join(joins)}
            GROUP BY s.id
            ORDER BY COALESCE(s.session_datetime, '') DESC, s.id DESC
            """
        ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            item = row_to_dict(row)
            dt_value = str(item.get("session_datetime") or "")
            item["session_datetime_label"] = _format_session_datetime_label(dt_value)
            month_key = dt_value[:7] if len(dt_value) >= 7 else "unbekannt"
            item["month_group"] = month_key
            item["month_group_label"] = _format_session_month_label(month_key)

            names: list[str] = []
            direct_name = next((str(item.get(key) or "").strip() for key in ("direct_label_de", "direct_final_name", "direct_display_name", "direct_canonical_name") if str(item.get(key) or "").strip()), "")
            if direct_name:
                names.append(direct_name)
            extra_names = str(item.get("session_target_names") or "").strip()
            if extra_names:
                for name in [part.strip() for part in extra_names.split(",")]:
                    if name and name not in names:
                        names.append(name)
            fallback_target = str(item.get("target") or "").strip()
            if not names and fallback_target:
                names.append(fallback_target)
            item["session_target_names_list"] = names
            item["session_target_names_label"] = " · ".join(names) if names else "Kein Session-Target"
            preview_id = item.get("dwarf_preview_raw_file_id")
            item["dwarf_preview_url"] = f"/media/raw-file/{int(preview_id)}" if preview_id else "/static/img/nopic_session.svg"
            item["session_href"] = f"/sessions/{int(item.get('id') or 0)}"
            items.append(item)
        return items
    finally:
        conn.close()


def _group_gallery_sessions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("month_group") or "unbekannt")
        if not groups or groups[-1]["key"] != key:
            groups.append({"key": key, "label": item.get("month_group_label") or "Unbekannt", "session_items": []})
        groups[-1]["session_items"].append(item)
    return groups


def _load_session_detail(session_id: int) -> dict[str, Any] | None:
    conn = db_conn()
    try:
        if not db_table_exists(conn, "sessions"):
            return None
        session_columns = set(db_table_columns(conn, "sessions"))
        has_targets = db_table_exists(conn, "targets")
        has_target_final = db_table_exists(conn, "target_final")
        has_session_targets = db_table_exists(conn, "session_targets")
        has_raw_files = db_table_exists(conn, "raw_files")
        select_parts = ["s.*"]
        joins: list[str] = []
        if "target_id" in session_columns and has_target_final:
            joins.append("LEFT JOIN target_final tf ON tf.target_id = s.target_id")
            select_parts.append("tf.final_name AS direct_final_name")
        else:
            select_parts.append("NULL AS direct_final_name")
        if "target_id" in session_columns and has_targets:
            joins.append("LEFT JOIN targets t ON t.id = s.target_id")
            select_parts.extend(["t.label_de AS direct_label_de", "t.display_name AS direct_display_name", "t.canonical_name AS direct_canonical_name"])
        else:
            select_parts.extend(["NULL AS direct_label_de", "NULL AS direct_display_name", "NULL AS direct_canonical_name"])
        row = conn.execute(f"SELECT {', '.join(select_parts)} FROM sessions s {' '.join(joins)} WHERE s.id = ? LIMIT 1", (session_id,)).fetchone()
        if row is None:
            return None
        item = row_to_dict(row)
        item["session_datetime_label"] = _format_session_datetime_label(item.get("session_datetime"))
        names: list[str] = []
        direct_name = next((str(item.get(key) or "").strip() for key in ("direct_label_de", "direct_final_name", "direct_display_name", "direct_canonical_name") if str(item.get(key) or "").strip()), "")
        if direct_name:
            names.append(direct_name)
        if has_session_targets:
            extra_rows = conn.execute("""
                SELECT st.target_name, t.label_de, tf.final_name, t.display_name, t.canonical_name
                FROM session_targets st
                LEFT JOIN targets t ON t.id = st.target_id
                LEFT JOIN target_final tf ON tf.target_id = st.target_id
                WHERE st.session_id = ?
                ORDER BY COALESCE(st.is_requested_target, 0) DESC, COALESCE(st.is_primary, 0) DESC, COALESCE(st.priority_rank, 99999), st.id
            """, (session_id,)).fetchall()
            for extra_row in extra_rows:
                extra = row_to_dict(extra_row)
                name = next((str(extra.get(key) or "").strip() for key in ("label_de", "final_name", "display_name", "canonical_name", "target_name") if str(extra.get(key) or "").strip()), "")
                if name and name not in names:
                    names.append(name)
        fallback_target = str(item.get("target") or "").strip()
        if not names and fallback_target:
            names.append(fallback_target)
        item["session_target_names_list"] = names
        item["session_target_names_label"] = " · ".join(names) if names else "Kein Session-Target"
        preview_id = None
        if has_raw_files:
            raw_columns = set(db_table_columns(conn, "raw_files"))
            if "session_key" in raw_columns:
                preview_checks: list[str] = []
                if "source_subtype" in raw_columns:
                    preview_checks.append("source_subtype = 'dwarf_preview'")
                if "derivative_kind" in raw_columns:
                    preview_checks.append("derivative_kind = 'dwarf_preview'")
                if "file_name" in raw_columns:
                    preview_checks.append("lower(file_name) IN ('stacked.jpg', 'stacked_thumbnail.jpg')")
                if preview_checks:
                    preview_row = conn.execute(f"SELECT id FROM raw_files WHERE session_key = ? AND ({' OR '.join(preview_checks)}) ORDER BY id DESC LIMIT 1", (item.get("session_key"),)).fetchone()
                    if preview_row is not None:
                        preview_id = preview_row["id"]
        item["dwarf_preview_url"] = f"/media/raw-file/{int(preview_id)}" if preview_id else "/static/img/nopic_session.svg"
        return item
    finally:
        conn.close()


def deepsky_targets(limit: int = 100) -> list[dict[str, Any]]:
    return _load_target_cards(
        "lower(coalesce(t.category,'')) not in ('sun','moon')",
        (),
        limit,
    )


def system_targets(limit: int = 50) -> list[dict[str, Any]]:
    return _load_target_cards(
        "lower(coalesce(t.category,'')) in ('sun','moon')",
        (),
        limit,
    )


def db_list_table(
    conn: sqlite3.Connection,
    table: str,
    limit: int,
    offset: int,
    sort: str,
    order: str,
    q: str,
) -> dict[str, Any]:
    table_cfg = build_table_config(conn)
    if table not in table_cfg:
        raise ValueError("unknown table")
    if not db_table_exists(conn, table):
        raise ValueError("table missing")

    columns = db_table_columns(conn, table)
    if sort not in columns:
        sort = table_cfg[table]["default_sort"]
    order = "DESC" if order.upper() == "DESC" else "ASC"

    where_parts: list[str] = []
    params: list[Any] = []

    if q:
        like_value = f"%{q}%"
        search_columns = [c for c in table_cfg[table]["search_columns"] if c in columns]
        if search_columns:
            where_parts.append(
                "(" + " OR ".join([f"CAST({col} AS TEXT) LIKE ?" for col in search_columns]) + ")"
            )
            params.extend([like_value] * len(search_columns))

    for key, value in request.args.items():
        if not key.startswith("filter_"):
            continue
        col = key.removeprefix("filter_")
        if col not in columns or value.strip() == "":
            continue
        where_parts.append(f"CAST({col} AS TEXT) = ?")
        params.append(value.strip())

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM {table} {where_sql}",
        params,
    ).fetchone()["n"]

    rows = conn.execute(
        f"""
        SELECT *
        FROM {table}
        {where_sql}
        ORDER BY {sort} {order}
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    prev_offset = max(0, offset - limit)
    next_offset = offset + limit

    return {
        "table": table,
        "columns": columns,
        "total": total,
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "order": order,
        "q": q,
        "rows": [row_to_dict(r) for r in rows],
        "has_prev": offset > 0,
        "has_next": next_offset < total,
        "prev_offset": prev_offset,
        "next_offset": next_offset,
        "page_current": (offset // limit) + 1 if limit > 0 else 1,
        "page_total": max(1, ((total - 1) // limit) + 1) if total else 1,
    }


@APP.get("/")
def index():
    latest = latest_web_log()

    selected_table = ""
    q = ""
    db_view = None

    conn = db_conn()
    try:
        table_cfg = build_table_config(conn)
        table_names = list(table_cfg.keys())

        selected_table = request.args.get("table", "sessions").strip()
        if selected_table not in table_cfg:
            if "sessions" in table_cfg:
                selected_table = "sessions"
            elif table_names:
                selected_table = table_names[0]
            else:
                selected_table = ""

        limit = parse_int_arg("limit", 25, 1, 200)
        offset = parse_int_arg("offset", 0, 0, 1_000_000)
        sort = parse_text_arg("sort", table_cfg.get(selected_table, {}).get("default_sort", "id"))
        order = parse_text_arg("order", "DESC")
        q = parse_text_arg("q", "")

        if selected_table and db_table_exists(conn, selected_table):
            db_view = db_list_table(conn, selected_table, limit, offset, sort, order, q)
    finally:
        conn.close()

    gallery_sessions = _load_gallery_sessions()
    gallery_session_groups = _group_gallery_sessions(gallery_sessions)
    program_info = load_program_info()

    return render_template(
        "index.html",
        latest_log=latest,
        runs=db_recent_runs(),
        deepsky_targets_view=deepsky_targets(),
        system_targets_view=system_targets(),
        gallery_sessions=gallery_sessions,
        gallery_session_groups=gallery_session_groups,
        db_tables=db_tables_summary(),
        db_selected_table=selected_table,
        db_view=db_view,
        db_query=q,
        service_state=summarize_service_state(),
        dev_assets=dev_assets(),
        program_info=program_info,
    )



@APP.get("/sessions/<int:session_id>")
def session_detail_page(session_id: int):
    session = _load_session_detail(session_id)
    if session is None:
        abort(404)
    return render_template("session_detail.html", session=session)


@APP.get("/targets/<int:target_id>")
def target_detail_page(target_id: int):
    target = _load_target_detail(target_id)
    if target is None:
        abort(404)
    return render_template("target_page.html", target=target)


@APP.get("/api/targets/<int:target_id>")
def api_target_detail(target_id: int):
    target = _load_target_detail(target_id)
    if target is None:
        return jsonify({"ok": False, "error": "target not found"}), 404
    return jsonify({"ok": True, "target": target})


@APP.get("/media/raw-file/<int:raw_file_id>")
def media_raw_file(raw_file_id: int):
    conn = db_conn()
    try:
        if not db_table_exists(conn, "raw_files"):
            abort(404)
        columns = set(db_table_columns(conn, "raw_files"))
        if "abs_path" not in columns:
            abort(404)
        row = conn.execute("SELECT abs_path FROM raw_files WHERE id = ? LIMIT 1", (raw_file_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404)

    path = Path(str(row["abs_path"] or "")).resolve()
    if not path.exists() or not path.is_file():
        abort(404)
    return send_file(path)


@APP.get("/api/progress/current")
def api_progress_current():
    return jsonify(get_live_progress())


@APP.get("/api/status")
def api_status():
    return jsonify(
        {
            "ok": True,
            "service": "astromanager-web",
            "raw_root": os.environ.get("RAW_ROOT", ""),
            "data_root": os.environ.get("DATA_ROOT", ""),
            "runtime_root": os.environ.get("RUNTIME_ROOT", ""),
            "log_root": os.environ.get("LOG_ROOT", ""),
            "db_path": str(DB_PATH),
            "recent_runs": db_recent_runs(),
        }
    )


@APP.get("/api/runs")
def api_runs():
    return jsonify({"ok": True, "runs": db_recent_runs()})


@APP.get("/api/db/tables")
def api_db_tables():
    return jsonify({"ok": True, "tables": db_tables_summary()})


@APP.get("/api/db/<table>")
def api_db_table(table: str):
    limit = parse_int_arg("limit", 50, 1, 500)
    offset = parse_int_arg("offset", 0, 0, 1_000_000)

    conn = db_conn()
    try:
        table_cfg = build_table_config(conn)
        sort = parse_text_arg("sort", table_cfg.get(table, {}).get("default_sort", "id"))
        order = parse_text_arg("order", "DESC")
        q = parse_text_arg("q", "")
        data = db_list_table(conn, table, limit, offset, sort, order, q)
        return jsonify({"ok": True, **data})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    except sqlite3.OperationalError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    finally:
        conn.close()


@APP.get("/api/db/<table>/<int:row_id>")
def api_db_row(table: str, row_id: int):
    conn = db_conn()
    try:
        table_cfg = build_table_config(conn)
        if table not in table_cfg:
            return jsonify({"ok": False, "error": "unknown table"}), 404
        if not db_table_exists(conn, table):
            return jsonify({"ok": False, "error": "table missing"}), 404

        columns = db_table_columns(conn, table)
        if "id" not in columns:
            return jsonify({"ok": False, "error": "table has no id column"}), 400

        row = conn.execute(
            f"SELECT * FROM {table} WHERE id = ? LIMIT 1",
            (row_id,),
        ).fetchone()
        if row is None:
            return jsonify({"ok": False, "error": "row not found"}), 404

        return jsonify({"ok": True, "table": table, "row": row_to_dict(row)})
    finally:
        conn.close()


@APP.get("/api/live/summary")
def api_live_summary():
    return jsonify({"ok": True, **summarize_service_state(), "progress": get_live_progress()})


@APP.get("/api/dev/files")
def api_dev_files():
    return jsonify({"ok": True, **dev_assets()})


@APP.get("/dev/archive")
def dev_archive_page():
    return render_template("dev_archive.html", dev_assets=dev_assets())


@APP.post("/api/dev/upload-core-zip")
def api_dev_upload_core_zip():
    upload = request.files.get("zip_file")
    if upload is None or not upload.filename:
        return jsonify({"ok": False, "error": "Keine ZIP-Datei empfangen."}), 400
    name = Path(upload.filename).name
    if not name.lower().endswith(".zip"):
        return jsonify({"ok": False, "error": "Nur ZIP-Dateien sind erlaubt."}), 400
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_ROOT / name
    upload.save(target)
    res = subprocess.run(["/app/bin/core_apply_zip.sh", str(target)], capture_output=True, text=True)
    ok = res.returncode == 0
    return jsonify({"ok": ok, "action": "upload_core_zip", "stdout": res.stdout, "stderr": res.stderr, "returncode": res.returncode, "details": {"upload_path": str(target), "project_core_root": str(PROJECT_CORE_ROOT)}}), (200 if ok else 500)


@APP.post("/api/dev/restore/<path:filename>")
def api_dev_restore_archive(filename: str):
    try:
        path = resolve_download("backup", filename)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Backup nicht gefunden."}), 404
    res = subprocess.run(["/app/bin/core_restore_zip.sh", str(path)], capture_output=True, text=True)
    ok = res.returncode == 0
    return jsonify({"ok": ok, "action": "restore_core_zip", "stdout": res.stdout, "stderr": res.stderr, "returncode": res.returncode, "details": {"zip_path": str(path)}}), (200 if ok else 500)


@APP.post("/api/dev/delete/<bucket>/<path:filename>")
def api_dev_delete_artifact(bucket: str, filename: str):
    try:
        path = resolve_download(bucket, filename)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Datei nicht gefunden."}), 404
    res = subprocess.run(["/app/bin/core_delete_artifact.sh", bucket, path.name], capture_output=True, text=True)
    ok = res.returncode == 0
    return jsonify({
        "ok": ok,
        "action": "delete_artifact",
        "stdout": res.stdout,
        "stderr": res.stderr,
        "returncode": res.returncode,
        "details": {
            "bucket": bucket,
            "filename": path.name,
            "message": f"{'Backup' if bucket == 'backup' else 'SQL-Dump'} gelöscht." if ok else "Löschen fehlgeschlagen.",
        },
    }), (200 if ok else 500)


@APP.get("/download/<bucket>/<path:filename>")
def download_file(bucket: str, filename: str):
    try:
        path = resolve_download(bucket, filename)
    except FileNotFoundError:
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)


@APP.post("/api/run/<action>")
def api_run(action: str):
    if action not in ACTION_HANDLERS:
        return jsonify({"ok": False, "error": "unknown action"}), 404

    subprocess.run([ASTROCTL, "db", "init"], capture_output=True, text=True)

    append_web_log(f"[web] trigger action={action}")
    result = ACTION_HANDLERS[action]()

    stdout = str(result.get("stdout", "") or "")
    stderr = str(result.get("stderr", "") or "")

    if stdout.strip():
        append_web_log(stdout.strip())
    if stderr.strip():
        append_web_log(stderr.strip())

    result["recent_runs"] = db_recent_runs()
    return jsonify(result)


if __name__ == "__main__":
    subprocess.run([ASTROCTL, "db", "init"], capture_output=True, text=True)
    APP.run(host="0.0.0.0", port=int(os.environ.get("WEB_PORT", "8080")), debug=False)
