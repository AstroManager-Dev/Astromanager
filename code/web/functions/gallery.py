from pathlib import Path
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

        detected_targets: list[dict[str, Any]] = []
        if has_session_targets:
            extra_rows = conn.execute("""
                SELECT
                    st.target_name,
                    st.object_type,
                    st.source,
                    st.is_requested_target,
                    st.is_primary,
                    st.is_major,
                    st.priority_rank,
                    st.score,
                    st.distance_to_center_deg,
                    st.in_frame_fraction,
                    st.angular_size_arcmin,
                    st.ra_deg,
                    st.dec_deg,
                    st.notes,
                    t.label_de,
                    tf.final_name,
                    t.display_name,
                    t.canonical_name
                FROM session_targets st
                LEFT JOIN targets t ON t.id = st.target_id
                LEFT JOIN target_final tf ON tf.target_id = st.target_id
                WHERE st.session_id = ?
                ORDER BY COALESCE(st.is_requested_target, 0) DESC,
                         COALESCE(st.is_primary, 0) DESC,
                         COALESCE(st.priority_rank, 99999),
                         st.id
            """, (session_id,)).fetchall()
            for extra_row in extra_rows:
                extra = row_to_dict(extra_row)
                name = next((str(extra.get(key) or "").strip() for key in ("label_de", "final_name", "display_name", "canonical_name", "target_name") if str(extra.get(key) or "").strip()), "")
                if name and name not in names:
                    names.append(name)
                if name:
                    detected_targets.append({
                        "name": name,
                        "object_type": str(extra.get("object_type") or "").strip(),
                        "source": str(extra.get("source") or "").strip(),
                        "is_requested_target": int(extra.get("is_requested_target") or 0),
                        "is_primary": int(extra.get("is_primary") or 0),
                        "is_major": int(extra.get("is_major") or 0),
                        "priority_rank": extra.get("priority_rank"),
                        "score": extra.get("score"),
                        "distance_to_center_deg": extra.get("distance_to_center_deg"),
                        "in_frame_fraction": extra.get("in_frame_fraction"),
                        "angular_size_arcmin": extra.get("angular_size_arcmin"),
                        "ra_deg": extra.get("ra_deg"),
                        "dec_deg": extra.get("dec_deg"),
                        "notes": str(extra.get("notes") or "").strip(),
                    })

        fallback_target = str(item.get("target") or "").strip()
        if not names and fallback_target:
            names.append(fallback_target)

        item["session_target_names_list"] = names
        item["session_target_names_label"] = " · ".join(names) if names else "Kein Session-Target"
        item["display_target_name"] = names[0] if names else "Unbenanntes Target"
        item["display_target_aliases"] = names[1:]
        item["detected_targets"] = detected_targets

        exp_value = item.get("exp")
        gain_value = item.get("gain")
        filter_value = str(item.get("filter_set") or "").strip()
        capture_bits: list[str] = []
        capture_bits.append(f"EXP {exp_value:g}s" if isinstance(exp_value, (int, float)) else "EXP —")
        capture_bits.append(f"Gain {int(gain_value)}" if isinstance(gain_value, (int, float)) else "Gain —")
        if filter_value and filter_value.lower() != "unknown":
            capture_bits.append(f"Filter {filter_value}")
        item["capture_meta_label"] = " · ".join(capture_bits)

        item["image_mode_default"] = "png"
        item["source_mode_default"] = "telescope"
        item["fits_viewer_ready"] = False
        item["fits_viewer_note"] = "FITS-Viewer wird nach Installation einer passenden Viewer-Komponente aktiviert."

        item["telescope_meta_items"] = []
        for label, value in (
            ("Session-Key", item.get("session_key")),
            ("Pfad", item.get("raw_session_path")),
            ("Frames", item.get("frame_count")),
            ("Gesamtgröße", item.get("total_bytes")),
            ("Kamera", item.get("camera")),
            ("Binning", item.get("binning")),
            ("Temperatur Ø", item.get("temp_avg")),
            ("Temperatur Min", item.get("temp_min")),
            ("Temperatur Max", item.get("temp_max")),
            ("Status", item.get("status")),
        ):
            if value not in (None, ""):
                display = f"{float(value):g} °C" if label.startswith("Temperatur") and isinstance(value, (int, float)) else str(value)
                if label == "Gesamtgröße" and isinstance(value, (int, float)):
                    size = float(value)
                    for unit in ("B", "KB", "MB", "GB", "TB"):
                        if size < 1024.0 or unit == "TB":
                            display = f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
                            break
                        size /= 1024.0
                item["telescope_meta_items"].append({"label": label, "value": display})

        item["astromanager_meta_items"] = []
        for label, value in (
            ("Plate Solve", item.get("platesolve_status")),
            ("Solve Engine", item.get("solve_engine")),
            ("FOV X", item.get("solve_fov_x_deg")),
            ("FOV Y", item.get("solve_fov_y_deg")),
            ("Rotation", item.get("solve_rotation_deg")),
            ("RA", item.get("solve_ra_deg")),
            ("DEC", item.get("solve_dec_deg")),
            ("Footprint Radius", item.get("footprint_radius_deg")),
            ("Solve Pass", item.get("solve_pass")),
            ("Solve Hinweis", item.get("solve_message")),
        ):
            if value not in (None, ""):
                if label in {"FOV X", "FOV Y", "Rotation", "RA", "DEC", "Footprint Radius"} and isinstance(value, (int, float)):
                    suffix = "°"
                    display = f"{float(value):g}{suffix}"
                else:
                    display = str(value)
                item["astromanager_meta_items"].append({"label": label, "value": display})

        raw_assets: list[dict[str, Any]] = []
        image_assets: list[dict[str, Any]] = []
        light_frames: list[dict[str, Any]] = []
        png_image_assets: list[dict[str, Any]] = []
        fits_assets: list[dict[str, Any]] = []
        if has_raw_files:
            raw_columns = set(db_table_columns(conn, "raw_files"))
            if "session_key" in raw_columns:
                raw_select_parts = [
                    "id", "file_name", "abs_path", "rel_path", "source_subtype", "derivative_kind", "file_role", "filter_set", "quality_flag", "is_current"
                ]
                optional_cols = ["header_exptime", "header_gain", "header_filter", "header_date_obs", "camera", "temp_c", "binning", "size_bytes", "mtime_epoch"]
                for col in optional_cols:
                    raw_select_parts.append(col if col in raw_columns else f"NULL AS {col}")
                raw_rows = conn.execute(
                    f"SELECT {', '.join(raw_select_parts)} FROM raw_files WHERE session_key = ? ORDER BY id DESC",
                    (item.get("session_key"),),
                ).fetchall()
                def asset_priority(entry: dict[str, Any]) -> tuple[int, int]:
                    file_name = str(entry.get("file_name") or "").lower()
                    source_subtype = str(entry.get("source_subtype") or "").lower()
                    derivative_kind = str(entry.get("derivative_kind") or "").lower()
                    ext = Path(file_name).suffix.lower()
                    if ext == ".png" and ("stack" in file_name or derivative_kind == "dwarf_stack"):
                        return (0, -int(entry.get("id") or 0))
                    if source_subtype == "dwarf_preview" or derivative_kind == "dwarf_preview":
                        return (1, -int(entry.get("id") or 0))
                    if file_name in {"stacked.jpg", "stacked_thumbnail.jpg"}:
                        return (2, -int(entry.get("id") or 0))
                    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}:
                        return (3, -int(entry.get("id") or 0))
                    if ext in {".fit", ".fits", ".fts"}:
                        return (4, -int(entry.get("id") or 0))
                    return (9, -int(entry.get("id") or 0))

                for raw_row in raw_rows:
                    raw_item = row_to_dict(raw_row)
                    file_name = str(raw_item.get("file_name") or "")
                    ext = Path(file_name).suffix.lower()
                    raw_item["media_href"] = f"/media/raw-file/{int(raw_item.get('id') or 0)}"
                    raw_item["path_label"] = str(raw_item.get("rel_path") or raw_item.get("abs_path") or "")
                    exptime = raw_item.get("header_exptime") if raw_item.get("header_exptime") not in (None, "") else raw_item.get("exp")
                    gain = raw_item.get("header_gain") if raw_item.get("header_gain") not in (None, "") else raw_item.get("gain")
                    filt = str(raw_item.get("header_filter") or raw_item.get("filter_set") or "").strip()
                    meta_bits: list[str] = []
                    if isinstance(exptime, (int, float)):
                        meta_bits.append(f"EXP {float(exptime):g}s")
                    if isinstance(gain, (int, float)):
                        meta_bits.append(f"Gain {float(gain):g}")
                    if filt and filt.lower() != "unknown":
                        meta_bits.append(f"Filter {filt}")
                    raw_item["meta_label"] = " · ".join(meta_bits)
                    raw_item["is_fits"] = ext in {".fit", ".fits", ".fts"}
                    raw_item["is_image"] = ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
                    raw_item["priority"] = asset_priority(raw_item)
                    raw_assets.append(raw_item)
                    if raw_item["is_fits"]:
                        fits_assets.append(raw_item)
                    if raw_item["is_image"]:
                        image_assets.append(raw_item)
                        png_image_assets.append(raw_item)
                    role = str(raw_item.get("file_role") or "").lower()
                    subtype = str(raw_item.get("source_subtype") or "").lower()
                    derivative_kind = str(raw_item.get("derivative_kind") or "").lower()
                    if role == "light" or subtype == "light" or (not derivative_kind and ext in {".fit", ".fits", ".fts"}):
                        light_frames.append(raw_item)

        image_assets.sort(key=lambda entry: entry.get("priority", (9, 0)))
        png_image_assets.sort(key=lambda entry: entry.get("priority", (9, 0)))
        fits_assets.sort(key=lambda entry: entry.get("priority", (9, 0)))
        light_frames.sort(key=lambda entry: (-int(entry.get("mtime_epoch") or 0), -int(entry.get("id") or 0)))

        primary_image = png_image_assets[0] if png_image_assets else None
        item["primary_image_asset"] = primary_image
        item["primary_image_url"] = primary_image.get("media_href") if primary_image else "/static/img/nopic_session.svg"
        item["image_gallery_items"] = png_image_assets[:4]
        item["fits_assets"] = fits_assets
        item["light_frames"] = light_frames[:24]
        item["raw_assets"] = raw_assets
        item["raw_assets_count"] = len(raw_assets)
        item["light_frames_count"] = len(light_frames)
        item["fits_available"] = bool(fits_assets)
        item["fits_preview_name"] = fits_assets[0].get("file_name") if fits_assets else ""
        item["dwarf_preview_url"] = item["primary_image_url"]
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
