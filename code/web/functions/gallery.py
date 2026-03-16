from typing import Any

from .database import db_conn, db_table_columns, db_table_exists, row_to_dict
from .formatters import _format_exposure_duration_label, _format_session_datetime_label, _format_session_group_label, _format_session_month_label


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
            WHERE COALESCE(s.session_type, '') = 'light_session'
              AND COALESCE(s.category, '') IN ('deepsky', 'moon', 'sun')
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
            category_value = str(item.get("category") or "").strip().lower()
            if not names and fallback_target:
                names.append(fallback_target)
            if not names and category_value in ("sun", "moon"):
                names.append("Solarsystem")
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

load_gallery_sessions = _load_gallery_sessions
group_gallery_sessions = _group_gallery_sessions


def _apply_solarsystem_target_fallback(item: dict[str, Any]) -> dict[str, Any]:
    names = list(item.get("session_target_names_list") or [])
    fallback_target = str(item.get("target") or "").strip()
    category_value = str(item.get("category") or "").strip().lower()

    if not names and fallback_target and fallback_target.lower() != "unbenanntes target":
        names.append(fallback_target)

    if not names and category_value in ("sun", "moon"):
        names.append("Solarsystem")

    item["session_target_names_list"] = names
    item["session_target_names_label"] = " · ".join(names) if names else "Kein Session-Target"
    return item


load_session_detail = _load_session_detail
