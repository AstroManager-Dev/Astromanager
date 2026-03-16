#!/usr/bin/env python3
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request, send_file

from actions import ACTION_HANDLERS
from progress_runtime import get_live_progress
from functions.common import ASTROCTL, PROJECT_CORE_ROOT, PROJECT_ROOT, UPLOAD_ROOT
from functions.database import (
    build_table_config,
    db_conn,
    db_list_table,
    db_recent_runs,
    db_table_columns,
    db_table_exists,
    db_tables_summary,
    parse_int_arg,
    parse_text_arg,
    row_to_dict,
)
from functions.gallery import (
    group_gallery_sessions,
    load_gallery_sessions,
    load_raw_file_detail,
    load_session_detail,
    load_session_raw_list,
)
from functions.program_info import load_program_info
from functions.status import append_web_log, dev_assets, latest_web_log, resolve_download, summarize_service_state
from functions.targets import deepsky_targets, load_target_detail, system_targets

APP = Flask(__name__)


@APP.context_processor
def inject_global_ui_context() -> dict[str, Any]:
    try:
        return {"program_info_global": load_program_info()}
    except Exception:
        return {"program_info_global": None}


@APP.context_processor
def inject_global_ui_context() -> dict[str, Any]:
    try:
        return {"program_info_global": load_program_info()}
    except Exception:
        return {"program_info_global": None}


@APP.context_processor
def inject_global_ui_context() -> dict[str, Any]:
    try:
        return {"program_info_global": load_program_info()}
    except Exception:
        return {"program_info_global": None}


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

    gallery_sessions = load_gallery_sessions()
    gallery_session_groups = group_gallery_sessions(gallery_sessions)
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
    session = load_session_detail(session_id)
    if session is None:
        abort(404)

    back = (request.args.get("back") or "").strip().lower()
    target_id = (request.args.get("target_id") or "").strip()

    if back == "target" and target_id.isdigit():
        session["back_href"] = f"/targets/{target_id}"
        session["back_label"] = "Zurück zu Target"
    else:
        session["back_href"] = "/#gallery"
        session["back_label"] = "Zurück zur Galerie"

    return render_template("session_detail.html", session=session)



@APP.get("/targets/<int:target_id>")
def target_detail_page(target_id: int):
    target = load_target_detail(target_id)
    if target is None:
        abort(404)
    return render_template("target_page.html", target=target)


@APP.get("/api/targets/<int:target_id>")
def api_target_detail(target_id: int):
    target = load_target_detail(target_id)
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
        path_expr = "COALESCE(abs_path, rel_path)" if {"abs_path", "rel_path"} <= columns else ("abs_path" if "abs_path" in columns else "rel_path")
        row = conn.execute(
            f"SELECT id, file_name, {path_expr} AS file_path FROM raw_files WHERE id = ? LIMIT 1",
            (raw_file_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404)

    item = row_to_dict(row)
    file_path = Path(str(item.get("file_path") or ""))
    if not file_path.exists() or not file_path.is_file():
        abort(404)

    return send_file(file_path)




@APP.get("/sessions/<int:session_id>/raw")
def session_raw_list_page(session_id: int):
    session = load_session_detail(session_id)
    if session is None:
        abort(404)
    source = (request.args.get("source") or "dwarf").strip().lower()
    page = parse_int_arg("page", 1, 1, 100000)
    page_size = parse_int_arg("page_size", 10, 1, 100)
    session = load_session_raw_list(session, source, page, page_size)
    return render_template("session_raw_list.html", session=session)


@APP.get("/raw-files/<int:raw_file_id>")
def raw_file_detail_page(raw_file_id: int):
    raw_file = load_raw_file_detail(raw_file_id)
    if raw_file is None:
        abort(404)
    return render_template("raw_file_detail.html", raw_file=raw_file)


@APP.get("/download/raw-file/<int:raw_file_id>")
def download_raw_file(raw_file_id: int):
    conn = db_conn()
    try:
        if not db_table_exists(conn, "raw_files"):
            abort(404)
        columns = set(db_table_columns(conn, "raw_files"))
        path_expr = "COALESCE(abs_path, rel_path)" if {"abs_path", "rel_path"} <= columns else ("abs_path" if "abs_path" in columns else "rel_path")
        row = conn.execute(
            f"SELECT id, file_name, {path_expr} AS file_path FROM raw_files WHERE id = ? LIMIT 1",
            (raw_file_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404)

    item = row_to_dict(row)
    file_path = Path(str(item.get("file_path") or ""))
    if not file_path.exists() or not file_path.is_file():
        abort(404)

    return send_file(file_path, as_attachment=True, download_name=str(item.get("file_name") or file_path.name))

@APP.get("/api/progress/current")
def api_progress_current():
    return jsonify({"ok": True, "progress": get_live_progress()})


@APP.get("/api/status")
def api_status():
    return jsonify({"ok": True, "status": summarize_service_state()})


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
