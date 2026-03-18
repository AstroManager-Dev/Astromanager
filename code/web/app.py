#!/usr/bin/env python3
import os
import secrets
import sqlite3
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_file, session, url_for

from actions import ACTION_HANDLERS
from progress_runtime import get_live_progress
from functions.common import ASTROCTL, CONFIG_ROOT, PROJECT_CORE_ROOT, PROJECT_ROOT, UPLOAD_ROOT
from functions.auth import (
    action_permission,
    admin_bootstrap_status,
    admin_set_user_password,
    admin_toggle_user_active,
    admin_update_user_role,
    authenticate_user,
    bootstrap_admin_password,
    build_login_info,
    build_login_page_data,
    create_user_by_admin,
    get_auth_context,
    has_permission,
    login_user_session,
    logout_user_session,
    require_permission,
    issue_csrf_token,
    validate_csrf_token,
)
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
from functions.fits_viewer import enrich_raw_file_viewer_context, render_raw_file_fits_preview
from functions.ephemeris import load_session_ephemeris_context
from functions.observing import assign_session_observing_site, create_observing_site, delete_observing_site, list_observing_sites, set_default_observing_site
from functions.program_info import load_program_info
from functions.status import append_web_log, dev_assets, latest_web_log, resolve_download, summarize_service_state
from functions.targets import deepsky_targets, load_target_detail, system_targets

APP = Flask(__name__)


def load_web_secret_key() -> str:
    secret_file = Path("/runtime/web_secret_key.txt")

    if secret_file.exists():
        value = secret_file.read_text(encoding="utf-8").strip()
        if value:
            return value

    secret_file.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(32)
    secret_file.write_text(value, encoding="utf-8")
    return value

    secret_file.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(32)
    secret_file.write_text(value, encoding="utf-8")
    return value
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(48)
    secret_file.write_text(value, encoding="utf-8")
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass
    return value


APP.secret_key = load_web_secret_key()
APP.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(os.environ.get("ASTROMANAGER_SECURE_COOKIE", "0") == "1"),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


def discover_css_modules() -> list[str]:
    candidate_roots = [
        Path(APP.static_folder or "") / "css" / "modules",
        PROJECT_ROOT / "code" / "web" / "static" / "css" / "modules",
        PROJECT_CORE_ROOT / "code" / "web" / "static" / "css" / "modules",
    ]
    for css_root in candidate_roots:
        if css_root.exists() and css_root.is_dir():
            files = [
                f"css/modules/{path.name}"
                for path in sorted(css_root.glob("*.css"))
                if path.is_file()
            ]
            if files:
                return files
    return []


@APP.context_processor
def inject_global_ui_context() -> dict[str, Any]:
    auth_context = get_auth_context()
    try:
        return {
            "program_info_global": load_program_info(),
            "css_module_files": discover_css_modules(),
            "auth_context_global": auth_context,
            "login_info_global": build_login_info(auth_context),
            "login_user": auth_context.get("display_name", "Gast"),
            "login_href": auth_context.get("action_href", "/login"),
        }
    except Exception:
        return {
            "program_info_global": None,
            "css_module_files": discover_css_modules(),
            "auth_context_global": auth_context,
            "login_info_global": build_login_info(auth_context),
            "login_user": auth_context.get("display_name", "Gast"),
            "login_href": auth_context.get("action_href", "/login"),
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


@APP.get("/settings")
def settings_page():
    auth_context = get_auth_context()
    requested_section = (request.args.get("section") or "").strip().lower()
    available_sections = ["devices", "sources", "display", "locations", "system", "info"]
    if requested_section not in available_sections:
        requested_section = "info" if not auth_context.get("can_manage_settings") else "devices"

    locked_sections = set()
    if not auth_context.get("can_manage_settings"):
        locked_sections = {"devices", "sources", "display", "locations", "system"}
        if requested_section in locked_sections:
            active_section = requested_section
        else:
            active_section = "info"
    else:
        active_section = requested_section

    return render_template(
        "settings_page.html",
        settings_active_section=active_section,
        settings_locked_sections=locked_sections,
        observing_sites=list_observing_sites(),
        csrf_token=issue_csrf_token(),
    )


def render_login_page(*, error: str = "", message: str = "", status_code: int = 200):
    auth_context = get_auth_context()
    page_data = build_login_page_data(auth_context, error=error, message=message)
    return render_template("login_page.html", **page_data), status_code


@APP.get("/login")
def login_page():
    return render_login_page()


@APP.post("/login")
def login_page_post():
    action = (request.form.get("action") or "login").strip().lower()
    if not validate_csrf_token(request.form.get("csrf_token")):
        return render_login_page(error="Die Sitzung ist abgelaufen oder das Formular ist ungültig.", status_code=400)

    auth_context = get_auth_context()

    if action == "bootstrap_admin":
        bootstrap = admin_bootstrap_status()
        if not bootstrap.get("bootstrap_needed"):
            return render_login_page(error="Der Admin-Login ist bereits initialisiert.", status_code=400)
        ok, message = bootstrap_admin_password(
            request.form.get("password") or "",
            request.form.get("password_confirm") or "",
        )
        if ok:
            return render_login_page(message=message)
        return render_login_page(error=message, status_code=400)

    if action == "login":
        ok, message, user = authenticate_user(
            request.form.get("username") or "",
            request.form.get("password") or "",
            request.remote_addr or "",
        )
        if ok and user is not None:
            login_user_session(user)
            return redirect(url_for("login_page"))
        return render_login_page(error=message, status_code=400)

    if action == "logout":
        logout_user_session()
        return redirect(url_for("login_page"))

    if action == "create_user":
        if not auth_context.get("can_manage_users"):
            abort(403)
        ok, message = create_user_by_admin(
            request.form.get("username") or "",
            request.form.get("display_name") or "",
            request.form.get("role") or "observer",
            request.form.get("password") or "",
            request.form.get("password_confirm") or "",
            str(auth_context.get("display_name") or "admin"),
        )
        return render_login_page(message=message) if ok else render_login_page(error=message, status_code=400)

    if action == "set_user_role":
        if not auth_context.get("can_manage_users"):
            abort(403)
        user_id = int(request.form.get("user_id") or "0")
        ok, message = admin_update_user_role(user_id, request.form.get("role") or "observer", str(auth_context.get("display_name") or "admin"))
        return render_login_page(message=message) if ok else render_login_page(error=message, status_code=400)

    if action == "set_user_password":
        if not auth_context.get("can_manage_users"):
            abort(403)
        user_id = int(request.form.get("user_id") or "0")
        ok, message = admin_set_user_password(user_id, request.form.get("password") or "", request.form.get("password_confirm") or "")
        return render_login_page(message=message) if ok else render_login_page(error=message, status_code=400)

    if action == "toggle_user_active":
        if not auth_context.get("can_manage_users"):
            abort(403)
        user_id = int(request.form.get("user_id") or "0")
        target_active = (request.form.get("target_active") or "1") == "1"
        ok, message = admin_toggle_user_active(user_id, target_active)
        return render_login_page(message=message) if ok else render_login_page(error=message, status_code=400)

    return render_login_page(error="Unbekannte Login-Aktion.", status_code=400)


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

    session.update(load_session_ephemeris_context(session))
    return render_template("session_detail.html", session=session, csrf_token=issue_csrf_token())



@APP.post("/settings/locations")
@require_permission("manage_settings")
def settings_locations_create():
    if not validate_csrf_token(request.form.get("csrf_token")):
        return redirect("/settings?section=locations")
    name = (request.form.get("name") or "").strip()
    timezone_name = (request.form.get("timezone_name") or "").strip()
    set_default = (request.form.get("set_default") or "") == "1"
    try:
        latitude_deg = float((request.form.get("latitude_deg") or "").strip())
        longitude_deg = float((request.form.get("longitude_deg") or "").strip())
        elevation_raw = (request.form.get("elevation_m") or "").strip()
        elevation_m = float(elevation_raw) if elevation_raw else None
    except ValueError:
        return redirect("/settings?section=locations")
    create_observing_site(name, latitude_deg, longitude_deg, elevation_m, timezone_name, set_default=set_default)
    return redirect("/settings?section=locations")


@APP.post("/settings/locations/<int:site_id>/default")
@require_permission("manage_settings")
def settings_locations_default(site_id: int):
    if validate_csrf_token(request.form.get("csrf_token")):
        set_default_observing_site(site_id)
    return redirect("/settings?section=locations")


@APP.post("/settings/locations/<int:site_id>/delete")
@require_permission("manage_settings")
def settings_locations_delete(site_id: int):
    if validate_csrf_token(request.form.get("csrf_token")):
        delete_observing_site(site_id)
    return redirect("/settings?section=locations")


@APP.post("/sessions/<int:session_id>/site")
def session_site_assign(session_id: int):
    if not get_auth_context().get("can_manage_settings"):
        abort(403)
    if not validate_csrf_token(request.form.get("csrf_token")):
        return redirect(f"/sessions/{session_id}")
    raw_site_id = (request.form.get("observing_site_id") or "").strip()
    assign_session_observing_site(session_id, int(raw_site_id) if raw_site_id.isdigit() else None)
    return redirect(f"/sessions/{session_id}")


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
    requested_view = request.args.get("view")
    if requested_view is None and raw_file.get("is_fits"):
        requested_view = "fits"
    raw_file = enrich_raw_file_viewer_context(
        raw_file,
        requested_view,
        request.args.get("debayer"),
        request.args.get("stretch"),
        request.args.get("black"),
        request.args.get("white"),
        request.args.get("gamma"),
        request.args.get("preset"),
    )
    return render_template("raw_file_detail.html", raw_file=raw_file)


@APP.get("/media/raw-file-fits-preview/<int:raw_file_id>.<string:fmt>")
def media_raw_file_fits_preview(raw_file_id: int, fmt: str):
    raw_file = load_raw_file_detail(raw_file_id)
    if raw_file is None or not raw_file.get("is_fits"):
        abort(404)
    if fmt not in {"png", "webp"}:
        abort(404)
    try:
        payload, mimetype = render_raw_file_fits_preview(
            raw_file,
            request.args.get("debayer"),
            request.args.get("stretch"),
            request.args.get("black"),
            request.args.get("white"),
            request.args.get("gamma"),
            request.args.get("kind"),
        )
    except FileNotFoundError:
        abort(404)
    return Response(payload, mimetype=mimetype)


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
@require_permission("view_database")
def api_db_tables():
    return jsonify({"ok": True, "tables": db_tables_summary()})


@APP.get("/api/db/<table>")
@require_permission("view_database")
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
@require_permission("view_database")
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
@require_permission("view_system_status")
def api_live_summary():
    return jsonify({"ok": True, **summarize_service_state(), "progress": get_live_progress()})


@APP.get("/api/dev/files")
@require_permission("manage_dev_tools")
def api_dev_files():
    return jsonify({"ok": True, **dev_assets()})


@APP.get("/dev/archive")
@require_permission("manage_dev_tools")
def dev_archive_page():
    return render_template("dev_archive.html", dev_assets=dev_assets())


@APP.post("/api/dev/upload-core-zip")
@require_permission("manage_dev_tools")
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
@require_permission("manage_dev_tools")
def api_dev_restore_archive(filename: str):
    try:
        path = resolve_download("backup", filename)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Backup nicht gefunden."}), 404
    res = subprocess.run(["/app/bin/core_restore_zip.sh", str(path)], capture_output=True, text=True)
    ok = res.returncode == 0
    return jsonify({"ok": ok, "action": "restore_core_zip", "stdout": res.stdout, "stderr": res.stderr, "returncode": res.returncode, "details": {"zip_path": str(path)}}), (200 if ok else 500)


@APP.post("/api/dev/delete/<bucket>/<path:filename>")
@require_permission("manage_dev_tools")
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
    if bucket in {"backup", "sql"} and not has_permission("manage_dev_tools"):
        abort(403)
    try:
        path = resolve_download(bucket, filename)
    except FileNotFoundError:
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)


@APP.post("/api/run/<action>")
def api_run(action: str):
    if action not in ACTION_HANDLERS:
        return jsonify({"ok": False, "error": "unknown action"}), 404

    required_permission = action_permission(action)
    if required_permission and not has_permission(required_permission):
        return jsonify({"ok": False, "error": "forbidden", "required_permission": required_permission}), 403

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


@APP.get("/forbidden")
def forbidden_route():
    auth_context = get_auth_context()
    return render_template("403.html", auth_context=auth_context), 403

@APP.errorhandler(403)
def forbidden_page(error):
    auth_context = get_auth_context()
    return render_template("403.html", auth_context=auth_context), 403

if __name__ == "__main__":
    subprocess.run([ASTROCTL, "db", "init"], capture_output=True, text=True)
    APP.run(host="0.0.0.0", port=int(os.environ.get("WEB_PORT", "8080")), debug=False)
