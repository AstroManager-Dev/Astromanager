import math
import sqlite3
from typing import Any

from .common import TARGET_THUMBNAIL_FILE_NAME, TARGET_THUMB_CENTER_RADIUS_FACTOR
from .database import db_conn, db_table_columns, db_table_exists, row_to_dict
from .formatters import _format_exposure_duration_label, _format_session_datetime_label, _format_session_group_label


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
            item["session_href"] = f"/sessions/{int(item.get('id') or 0)}?back=target&target_id={int(target_id)}"

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

load_target_detail = _load_target_detail
