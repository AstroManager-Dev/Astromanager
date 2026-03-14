#!/usr/bin/env python3
import os
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


def _load_target_cards(where_sql: str = "", params: tuple[Any, ...] = (), limit: int = 100) -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        if not db_table_exists(conn, "targets"):
            return []

        has_target_final = db_table_exists(conn, "target_final")
        has_session_targets = db_table_exists(conn, "session_targets")
        has_session_target_resolve_item = db_table_exists(conn, "session_target_resolve_item")

        sessions_join = ""
        if has_session_targets:
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
                    t.nasa_title,
                    t.nasa_page_url,
                    t.nasa_thumb_url,

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
                "wikidata_id",
            ]
            existing = [c for c in wanted if c in columns]
            if not existing:
                return []

            sort_col = "final_name" if "final_name" in columns else ("canonical_name" if "canonical_name" in columns else "id")
            where_clause = f"WHERE {where_sql}" if where_sql.strip() else ""

            rows = conn.execute(
                f"""
                SELECT {", ".join("t." + c for c in existing)},
                       COALESCE(sc.session_count, 0) AS session_count
                FROM targets t
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

            d["display_name"] = (d.get("final_name") or d.get("display_name") or d.get("canonical_name") or "").strip()
            d["subtitle"] = (d.get("canonical_name") or "").strip()
            d["objtype"] = (d.get("final_objtype") or d.get("objtype") or "").strip()

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

            items.append(d)
        return items
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

    return render_template(
        "index.html",
        latest_log=latest,
        runs=db_recent_runs(),
        deepsky_targets_view=deepsky_targets(),
        system_targets_view=system_targets(),
        db_tables=db_tables_summary(),
        db_selected_table=selected_table,
        db_view=db_view,
        db_query=q,
        service_state=summarize_service_state(),
        dev_assets=dev_assets(),
    )



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
