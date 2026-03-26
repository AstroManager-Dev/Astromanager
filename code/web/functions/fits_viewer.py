from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
from typing import Any

import numpy as np
from PIL import Image, features

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    cv2 = None

from .database import db_conn, db_table_exists, row_to_dict

DEFAULT_PRESET_KEY = "auto"
DEFAULT_BLACK = 0.5
DEFAULT_WHITE = 99.5
DEFAULT_GAMMA = 1.0
DEFAULT_STRETCH = "auto"
DEFAULT_DEBAYER = "auto"
VALID_STRETCH_MODES = {"auto", "linear", "arcsinh"}
VALID_DEBAYER_MODES = {"auto", "mono", "rggb", "bggr", "grbg", "gbrg"}


def _normalize_view_mode(value: str | None, is_fits: bool) -> str:
    default_mode = "fits" if is_fits else "file"
    mode = (value or default_mode).strip().lower()
    if is_fits:
        return "fits" if mode == "fits" else default_mode
    return "file"


def _normalize_debayer_mode(value: str | None) -> str:
    mode = (value or DEFAULT_DEBAYER).strip().lower()
    return mode if mode in VALID_DEBAYER_MODES else DEFAULT_DEBAYER


def _normalize_stretch_mode(value: str | None) -> str:
    mode = (value or DEFAULT_STRETCH).strip().lower()
    return mode if mode in VALID_STRETCH_MODES else DEFAULT_STRETCH


def _normalize_render_kind(value: str | None) -> str:
    kind = (value or "detail").strip().lower()
    return kind if kind in {"detail", "thumb"} else "detail"


def _parse_float(value: str | None, default: float, minimum: float, maximum: float) -> float:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, parsed))


def _format_float(value: float, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}"


def _supports_webp() -> bool:
    try:
        return bool(features.check("webp"))
    except Exception:
        return False


def _preview_extension() -> str:
    return "webp" if _supports_webp() else "png"


def _preview_mimetype() -> str:
    return "image/webp" if _supports_webp() else "image/png"


def _slugify_preset_label(value: str) -> str:
    label = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return label or "preset"


def _load_fits_viewer_presets(user_id: int | None = None) -> list[dict[str, Any]]:
    conn = db_conn()
    rows: list[dict[str, Any]] = []
    try:
        if db_table_exists(conn, "fits_viewer_presets"):
            system_rows = conn.execute(
                """
                SELECT id, preset_key, label, description, sort_order, is_active,
                       debayer_mode, stretch_mode, black_value, white_value, gamma_value
                FROM fits_viewer_presets
                WHERE is_active = 1
                ORDER BY sort_order ASC, label COLLATE NOCASE ASC
                """
            ).fetchall()
            for row in system_rows:
                item = row_to_dict(row)
                item["source"] = "system"
                item["select_key"] = str(item.get("preset_key") or "").strip().lower()
                item["preset_id"] = int(item.get("id") or 0)
                rows.append(item)

        if user_id and db_table_exists(conn, "user_fits_viewer_presets"):
            user_rows = conn.execute(
                """
                SELECT id, preset_key, label, description, sort_order, is_active,
                       debayer_mode, stretch_mode, black_value, white_value, gamma_value,
                       user_id
                FROM user_fits_viewer_presets
                WHERE is_active = 1 AND user_id = ?
                ORDER BY sort_order ASC, label COLLATE NOCASE ASC
                """,
                (int(user_id),),
            ).fetchall()
            for row in user_rows:
                item = row_to_dict(row)
                item["source"] = "user"
                item["select_key"] = f"user:{int(item.get('id') or 0)}"
                item["preset_id"] = int(item.get("id") or 0)
                rows.append(item)
        return rows
    finally:
        conn.close()


def _next_user_preset_key(conn, user_id: int, label: str, exclude_id: int | None = None) -> str:
    base_key = _slugify_preset_label(label)
    candidate = base_key
    suffix = 2
    while True:
        sql = "SELECT id FROM user_fits_viewer_presets WHERE user_id = ? AND preset_key = ?"
        params: list[Any] = [int(user_id), candidate]
        if exclude_id:
            sql += " AND id != ?"
            params.append(int(exclude_id))
        sql += " LIMIT 1"
        row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            return candidate
        candidate = f"{base_key}-{suffix}"
        suffix += 1


def save_user_fits_viewer_preset(
    user_id: int,
    label: str,
    debayer_mode: str,
    stretch_mode: str,
    black_value: str | float,
    white_value: str | float,
    gamma_value: str | float,
    overwrite_preset_id: int | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    owner_id = int(user_id or 0)
    if owner_id <= 0:
        return False, "Nur angemeldete Benutzer können eigene Presets speichern.", None

    preset_label = str(label or "").strip()
    if not preset_label:
        return False, "Preset-Name fehlt.", None
    if len(preset_label) > 80:
        preset_label = preset_label[:80].strip()

    debayer_value = _normalize_debayer_mode(str(debayer_mode or DEFAULT_DEBAYER))
    stretch_value = _normalize_stretch_mode(str(stretch_mode or DEFAULT_STRETCH))
    black_num = _parse_float(str(black_value), DEFAULT_BLACK, 0.0, 25.0)
    white_num = _parse_float(str(white_value), DEFAULT_WHITE, 75.0, 100.0)
    gamma_num = _parse_float(str(gamma_value), DEFAULT_GAMMA, 0.2, 4.0)

    conn = db_conn()
    try:
        if not db_table_exists(conn, "user_fits_viewer_presets"):
            return False, "User-Preset-Tabelle fehlt. Migration noch nicht eingespielt.", None

        if overwrite_preset_id:
            row = conn.execute(
                "SELECT id, preset_key FROM user_fits_viewer_presets WHERE id = ? AND user_id = ? LIMIT 1",
                (int(overwrite_preset_id), owner_id),
            ).fetchone()
            if row is None:
                return False, "Eigenes Preset zum Überschreiben nicht gefunden.", None
            preset_id = int(row[0])
            preset_key = _next_user_preset_key(conn, owner_id, preset_label, exclude_id=preset_id)
            conn.execute(
                """
                UPDATE user_fits_viewer_presets
                SET preset_key = ?,
                    label = ?,
                    debayer_mode = ?,
                    stretch_mode = ?,
                    black_value = ?,
                    white_value = ?,
                    gamma_value = ?,
                    updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
                """,
                (preset_key, preset_label, debayer_value, stretch_value, black_num, white_num, gamma_num, preset_id, owner_id),
            )
            conn.commit()
            return True, "Preset überschrieben.", {"id": preset_id, "select_key": f"user:{preset_id}", "label": preset_label}

        preset_key = _next_user_preset_key(conn, owner_id, preset_label)
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 1000) + 10 FROM user_fits_viewer_presets WHERE user_id = ?",
            (owner_id,),
        ).fetchone()
        sort_order = int((row[0] if row is not None else 1010) or 1010)
        cur = conn.execute(
            """
            INSERT INTO user_fits_viewer_presets (
                user_id, preset_key, label, description, sort_order, is_active,
                debayer_mode, stretch_mode, black_value, white_value, gamma_value,
                created_at, updated_at
            ) VALUES (?, ?, ?, '', ?, 1, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (owner_id, preset_key, preset_label, sort_order, debayer_value, stretch_value, black_num, white_num, gamma_num),
        )
        conn.commit()
        preset_id = int(cur.lastrowid)
        return True, "Preset gespeichert.", {"id": preset_id, "select_key": f"user:{preset_id}", "label": preset_label}
    finally:
        conn.close()


def delete_user_fits_viewer_preset(user_id: int, preset_id: int) -> tuple[bool, str]:
    owner_id = int(user_id or 0)
    target_id = int(preset_id or 0)
    if owner_id <= 0 or target_id <= 0:
        return False, "Preset konnte nicht gelöscht werden."
    conn = db_conn()
    try:
        if not db_table_exists(conn, "user_fits_viewer_presets"):
            return False, "User-Preset-Tabelle fehlt. Migration noch nicht eingespielt."
        row = conn.execute(
            "SELECT id FROM user_fits_viewer_presets WHERE id = ? AND user_id = ? LIMIT 1",
            (target_id, owner_id),
        ).fetchone()
        if row is None:
            return False, "Eigenes Preset nicht gefunden."
        conn.execute("DELETE FROM user_fits_viewer_presets WHERE id = ? AND user_id = ?", (target_id, owner_id))
        conn.commit()
        return True, "Preset gelöscht."
    finally:
        conn.close()

def _auto_preset_key(raw_file: dict[str, Any]) -> str:
    session = raw_file.get("session")
    session_data = session if isinstance(session, dict) else {}
    category = str(session_data.get("category") or raw_file.get("category") or "").strip().lower()
    target_name = str(session_data.get("target") or raw_file.get("header_object") or raw_file.get("display_name") or "").strip().lower()
    filter_name = str(raw_file.get("header_filter") or raw_file.get("filter_set") or "").strip().lower()
    exposure = raw_file.get("header_exptime") if raw_file.get("header_exptime") not in (None, "") else raw_file.get("exp")
    try:
        exposure_value = float(exposure or 0.0)
    except Exception:
        exposure_value = 0.0

    moon_planet_terms = {"moon", "mond", "sun", "sonne", "jupiter", "saturn", "mars", "venus", "mercury"}
    nebula_terms = ("duo", "dual", "ha", "h-alpha", "oiii", "sii", "narrow", "nebula")

    if category in {"moon", "sun", "planet", "solar_system"} or any(term in target_name for term in moon_planet_terms):
        return "moon_planet"
    if any(term in filter_name for term in nebula_terms) or exposure_value >= 30.0:
        return "nebula"
    if bool(raw_file.get("is_color_sensor")) or bool(raw_file.get("debayer_required")) or str(raw_file.get("header_bayerpat") or "").strip():
        return "neutral"
    return "neutral"


def _build_preset_map(raw_file: dict[str, Any], user_id: int | None = None) -> dict[str, dict[str, Any]]:
    rows = _load_fits_viewer_presets(user_id)
    preset_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("select_key") or row.get("preset_key") or "").strip().lower()
        if not key:
            continue
        preset_map[key] = {
            "key": key,
            "label": str(row.get("label") or key.title()),
            "description": str(row.get("description") or "").strip(),
            "debayer_mode": _normalize_debayer_mode(str(row.get("debayer_mode") or DEFAULT_DEBAYER)),
            "stretch_mode": _normalize_stretch_mode(str(row.get("stretch_mode") or DEFAULT_STRETCH)),
            "black_value": _parse_float(str(row.get("black_value") or DEFAULT_BLACK), DEFAULT_BLACK, 0.0, 25.0),
            "white_value": _parse_float(str(row.get("white_value") or DEFAULT_WHITE), DEFAULT_WHITE, 75.0, 100.0),
            "gamma_value": _parse_float(str(row.get("gamma_value") or DEFAULT_GAMMA), DEFAULT_GAMMA, 0.2, 4.0),
            "source": str(row.get("source") or "system"),
            "preset_id": int(row.get("preset_id") or row.get("id") or 0),
            "owner_user_id": int(row.get("user_id") or 0),
        }
    if DEFAULT_PRESET_KEY not in preset_map:
        preset_map[DEFAULT_PRESET_KEY] = {
            "key": DEFAULT_PRESET_KEY,
            "label": "Auto",
            "description": "Automatische Auswahl anhand der RAW-Metadaten.",
            "debayer_mode": DEFAULT_DEBAYER,
            "stretch_mode": DEFAULT_STRETCH,
            "black_value": DEFAULT_BLACK,
            "white_value": DEFAULT_WHITE,
            "gamma_value": DEFAULT_GAMMA,
            "source": "system",
            "preset_id": 0,
            "owner_user_id": 0,
        }
    resolved_auto_key = _auto_preset_key(raw_file)
    if resolved_auto_key in preset_map:
        auto_base = preset_map[resolved_auto_key]
        preset_map[DEFAULT_PRESET_KEY] = {
            **preset_map[DEFAULT_PRESET_KEY],
            "resolved_key": resolved_auto_key,
            "resolved_label": str(auto_base.get("label") or resolved_auto_key.title()),
            "debayer_mode": auto_base["debayer_mode"],
            "stretch_mode": auto_base["stretch_mode"],
            "black_value": auto_base["black_value"],
            "white_value": auto_base["white_value"],
            "gamma_value": auto_base["gamma_value"],
        }
    return preset_map


def _is_close(a: float, b: float, tol: float = 0.005) -> bool:
    return abs(float(a) - float(b)) <= tol


def _active_preset_key(
    selected_key: str,
    preset_map: dict[str, dict[str, Any]],
    debayer_mode: str,
    stretch_mode: str,
    black_value: float,
    white_value: float,
    gamma_value: float,
) -> str:
    preset = preset_map.get(selected_key)
    if preset is None:
        return "custom"
    matches = (
        preset.get("debayer_mode") == debayer_mode
        and preset.get("stretch_mode") == stretch_mode
        and _is_close(float(preset.get("black_value") or 0.0), black_value)
        and _is_close(float(preset.get("white_value") or 0.0), white_value)
        and _is_close(float(preset.get("gamma_value") or 0.0), gamma_value)
    )
    return selected_key if matches else "custom"


def enrich_raw_file_viewer_context(
    raw_file: dict[str, Any],
    view: str | None = None,
    debayer: str | None = None,
    stretch: str | None = None,
    black: str | None = None,
    white: str | None = None,
    gamma: str | None = None,
    preset: str | None = None,
    auth_user_id: int | None = None,
) -> dict[str, Any]:
    item = dict(raw_file)
    is_fits = bool(item.get("is_fits"))
    view_mode = _normalize_view_mode(view, is_fits)
    preset_key = (preset or DEFAULT_PRESET_KEY).strip().lower() or DEFAULT_PRESET_KEY
    preset_map = _build_preset_map(item, auth_user_id)
    base_preset = preset_map.get(preset_key) or preset_map.get(DEFAULT_PRESET_KEY) or {
        "key": DEFAULT_PRESET_KEY,
        "label": "Auto",
        "debayer_mode": DEFAULT_DEBAYER,
        "stretch_mode": DEFAULT_STRETCH,
        "black_value": DEFAULT_BLACK,
        "white_value": DEFAULT_WHITE,
        "gamma_value": DEFAULT_GAMMA,
    }

    debayer_mode = _normalize_debayer_mode(debayer or str(base_preset.get("debayer_mode") or DEFAULT_DEBAYER))
    stretch_mode = _normalize_stretch_mode(stretch or str(base_preset.get("stretch_mode") or DEFAULT_STRETCH))
    black_value_num = _parse_float(black, float(base_preset.get("black_value") or DEFAULT_BLACK), 0.0, 25.0)
    white_value_num = _parse_float(white, float(base_preset.get("white_value") or DEFAULT_WHITE), 75.0, 100.0)
    gamma_value_num = _parse_float(gamma, float(base_preset.get("gamma_value") or DEFAULT_GAMMA), 0.2, 4.0)

    black_value = _format_float(black_value_num, 2)
    white_value = _format_float(white_value_num, 2)
    gamma_value = _format_float(gamma_value_num, 2)
    raw_file_id = int(item.get("id") or 0)
    preview_ext = _preview_extension()
    file_name_lower = str(item.get("file_name") or "").strip().lower()
    suffix_lower = Path(file_name_lower).suffix.lower()
    is_tiff = suffix_lower in {".tif", ".tiff"} or file_name_lower.endswith((".tif", ".tiff"))

    viewer_query = (
        f"preset={preset_key}&debayer={debayer_mode}&stretch={stretch_mode}"
        f"&black={black_value}&white={white_value}&gamma={gamma_value}"
    )

    active_preset_key = _active_preset_key(
        preset_key,
        preset_map,
        debayer_mode,
        stretch_mode,
        black_value_num,
        white_value_num,
        gamma_value_num,
    )
    current_preset = preset_map.get(preset_key)
    current_preset_select_key = preset_key if current_preset is not None else (active_preset_key if active_preset_key in preset_map else "custom")
    selected_preset_key = active_preset_key
    selected_preset_label = "Custom" if selected_preset_key == "custom" else str((preset_map.get(selected_preset_key) or {}).get("label") or selected_preset_key.title())
    current_preset_source = str((current_preset or {}).get("source") or "")
    current_preset_id = int((current_preset or {}).get("preset_id") or 0)
    current_preset_label = str((current_preset or {}).get("label") or "")
    current_preset_is_user = current_preset_source == "user" and current_preset_id > 0
    current_preset_modified = bool(current_preset is not None and selected_preset_key == "custom")

    preset_options = [
        {
            "key": key,
            "label": str(preset_row.get("label") or key.title()),
            "selected": key == current_preset_select_key,
            "resolved_label": str(preset_row.get("resolved_label") or "").strip(),
            "debayer_mode": str(preset_row.get("debayer_mode") or DEFAULT_DEBAYER),
            "stretch_mode": str(preset_row.get("stretch_mode") or DEFAULT_STRETCH),
            "black_value": _format_float(float(preset_row.get("black_value") or DEFAULT_BLACK), 2),
            "white_value": _format_float(float(preset_row.get("white_value") or DEFAULT_WHITE), 2),
            "gamma_value": _format_float(float(preset_row.get("gamma_value") or DEFAULT_GAMMA), 2),
            "source": str(preset_row.get("source") or "system"),
            "preset_id": int(preset_row.get("preset_id") or 0),
            "is_user": str(preset_row.get("source") or "") == "user",
        }
        for key, preset_row in sorted(preset_map.items(), key=lambda item: (0 if str(item[1].get("source") or "system") == "system" and item[0] == DEFAULT_PRESET_KEY else 1 if str(item[1].get("source") or "system") == "system" else 2, str(item[1].get("label") or "")))
    ]

    is_image_preview = bool(item.get("is_image_preview"))
    viewer_type = "fits" if is_fits else ("image" if is_image_preview else "none")
    image_preview_url = str(item.get("raster_preview_url") or item.get("media_url") or "").strip()

    item.update(
        {
            "view_mode": view_mode,
            "viewer_type": viewer_type,
            "preset_key": preset_key,
            "selected_preset_key": selected_preset_key,
            "selected_preset_label": selected_preset_label,
            "current_preset_key": current_preset_select_key,
            "current_preset_label": current_preset_label or selected_preset_label,
            "current_preset_source": current_preset_source,
            "current_preset_id": current_preset_id,
            "current_preset_is_user": current_preset_is_user,
            "current_preset_modified": current_preset_modified,
            "fits_preset_options": preset_options,
            "debayer_mode": debayer_mode,
            "stretch_mode": stretch_mode,
            "black_value": black_value,
            "white_value": white_value,
            "gamma_value": gamma_value,
            "view_file_href": f"/raw-files/{raw_file_id}?view=file",
            "view_fits_href": f"/raw-files/{raw_file_id}?view=fits&{viewer_query}",
            "fits_preview_url": f"/media/raw-file-fits-preview/{raw_file_id}.{preview_ext}?{viewer_query}&kind=detail",
            "fits_thumb_url": f"/media/raw-file-fits-preview/{raw_file_id}.{preview_ext}?preset={preset_key}&debayer={debayer_mode}&stretch={stretch_mode}&black={black_value}&white={white_value}&gamma={gamma_value}&kind=thumb",
            "fits_preview_format": preview_ext.upper(),
            "fits_viewer_available": is_fits,
            "is_tiff_preview": is_tiff,
            "image_preview_url": f"/media/raw-file-raster-preview/{raw_file_id}.{preview_ext}" if is_tiff else item.get("media_url"),
            "fits_viewer_note": f"Serverseitige Vorschau mit OpenCV-Debayer, Presets, Stretch und {preview_ext.upper()}-Ausgabe.",
            "viewer_preview_url": f"/media/raw-file-fits-preview/{raw_file_id}.{preview_ext}?{viewer_query}&kind=detail" if is_fits else image_preview_url,
            "viewer_fullscreen_url": f"/media/raw-file-fits-preview/{raw_file_id}.{preview_ext}?{viewer_query}&kind=detail" if is_fits else image_preview_url,
            "viewer_format_label": preview_ext.upper() if is_fits else str(item.get("extension") or item.get("file_ext") or "Bild").replace(".", "").upper(),
            "viewer_state": {
                "view": "fits" if is_fits else "file",
                "preset": current_preset_select_key if current_preset_select_key != "custom" else "",
                "debayer": debayer_mode,
                "stretch": stretch_mode,
                "black": black_value,
                "white": white_value,
                "gamma": gamma_value,
            },
        }
    )
    if is_tiff:
        item["media_url"] = str(item.get("image_preview_url") or item.get("media_url") or "")
    return item


def _resolve_fits_path(raw_file: dict[str, Any]) -> Path:
    for key in ("abs_path", "rel_path"):
        value = str(raw_file.get(key) or "").strip()
        if value:
            path = Path(value)
            if path.exists() and path.is_file():
                return path
    raise FileNotFoundError("FITS file path not found")


def _read_hdu_data(hdu) -> np.ndarray | None:
    try:
        data = hdu.data
    except Exception:
        return None
    if data is None:
        return None
    return np.asarray(data)


def _find_first_image_hdu(hdul) -> tuple[np.ndarray, dict[str, Any]]:
    for hdu in hdul:
        array = _read_hdu_data(hdu)
        if array is None or array.size == 0:
            continue
        return array, dict(getattr(hdu, "header", {}) or {})
    raise ValueError("No FITS image data found")


def _prepare_array(array: np.ndarray) -> np.ndarray:
    data = np.asarray(array)
    while data.ndim > 2:
        if data.shape[0] in {3, 4}:
            data = np.moveaxis(data, 0, -1)
            break
        data = data[0]
    if data.ndim == 2:
        return data.astype(np.float32, copy=False)
    if data.ndim == 3 and data.shape[-1] in {3, 4}:
        return data[..., :3].astype(np.float32, copy=False)
    raise ValueError("Unsupported FITS dimensions")


def _channel_masks(height: int, width: int, pattern: str, xoff: int = 0, yoff: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    yy, xx = np.indices((height, width))
    row = (yy + int(yoff or 0)) % 2
    col = (xx + int(xoff or 0)) % 2
    pattern = (pattern or "RGGB").upper()
    if pattern == "BGGR":
        r = (row == 1) & (col == 1)
        b = (row == 0) & (col == 0)
    elif pattern == "GBRG":
        r = (row == 1) & (col == 0)
        b = (row == 0) & (col == 1)
    elif pattern == "GRBG":
        r = (row == 0) & (col == 1)
        b = (row == 1) & (col == 0)
    else:
        r = (row == 0) & (col == 0)
        b = (row == 1) & (col == 1)
    g = ~(r | b)
    return r, g, b


def _fill_channel(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    h, w = values.shape
    padded_values = np.pad(values, 1, mode="edge")
    padded_mask = np.pad(mask.astype(np.float32), 1, mode="edge")
    acc = np.zeros((h, w), dtype=np.float32)
    count = np.zeros((h, w), dtype=np.float32)
    for dy in range(3):
        for dx in range(3):
            win_values = padded_values[dy : dy + h, dx : dx + w]
            win_mask = padded_mask[dy : dy + h, dx : dx + w]
            acc += win_values * win_mask
            count += win_mask
    out = np.divide(acc, count, out=np.zeros_like(acc), where=count > 0)
    out[mask] = values[mask]
    return out


def _debayer_bayer(data: np.ndarray, pattern: str, xoff: int = 0, yoff: int = 0) -> np.ndarray:
    values = np.asarray(data, dtype=np.float32)
    r_mask, g_mask, b_mask = _channel_masks(values.shape[0], values.shape[1], pattern, xoff, yoff)
    r = _fill_channel(np.where(r_mask, values, 0.0), r_mask)
    g = _fill_channel(np.where(g_mask, values, 0.0), g_mask)
    b = _fill_channel(np.where(b_mask, values, 0.0), b_mask)
    return np.stack([r, g, b], axis=-1)


def _opencv_bayer_code(pattern: str) -> int | None:
    if cv2 is None:
        return None
    mapping = {
        "RGGB": getattr(cv2, "COLOR_BAYER_RG2RGB", None),
        "BGGR": getattr(cv2, "COLOR_BAYER_BG2RGB", None),
        "GRBG": getattr(cv2, "COLOR_BAYER_GR2RGB", None),
        "GBRG": getattr(cv2, "COLOR_BAYER_GB2RGB", None),
    }
    return mapping.get((pattern or "RGGB").upper())


def _detect_bayer_pattern(raw_file: dict[str, Any], header: dict[str, Any], requested_mode: str) -> str:
    requested = (requested_mode or "auto").strip().lower()
    if requested in {"rggb", "bggr", "grbg", "gbrg"}:
        return requested.upper()
    pattern = str(raw_file.get("header_bayerpat") or header.get("BAYERPAT") or "").strip().upper()
    return pattern if pattern in {"RGGB", "BGGR", "GRBG", "GBRG"} else "RGGB"


def _opencv_debayer(data: np.ndarray, pattern: str) -> np.ndarray | None:
    if cv2 is None:
        return None
    code = _opencv_bayer_code(pattern)
    if code is None:
        return None
    values = np.asarray(data, dtype=np.float32)
    finite = np.isfinite(values)
    if not finite.any():
        return None
    lo = float(np.nanpercentile(values[finite], 0.1))
    hi = float(np.nanpercentile(values[finite], 99.9))
    if hi <= lo:
        hi = lo + 1.0
    scaled = np.clip((values - lo) / (hi - lo), 0.0, 1.0)
    source = np.clip(scaled * 65535.0, 0, 65535).astype(np.uint16)
    rgb = cv2.cvtColor(source, code)
    return rgb.astype(np.float32) / 65535.0


def _background_neutralize(rgb: np.ndarray) -> np.ndarray:
    arr = np.asarray(rgb, dtype=np.float32)
    if arr.ndim != 3 or arr.shape[-1] != 3:
        return arr
    out = arr.copy()
    channel_medians = []
    for idx in range(3):
        channel = out[..., idx]
        finite = np.isfinite(channel)
        if not finite.any():
            channel_medians.append(1.0)
            continue
        channel_medians.append(float(np.nanpercentile(channel[finite], 30.0)))
    target = float(np.median(channel_medians)) if channel_medians else 1.0
    if target <= 0:
        return out
    for idx, median in enumerate(channel_medians):
        if median > 0:
            out[..., idx] *= target / median
    return out


def _reduce_green(rgb: np.ndarray, strength: float = 0.55) -> np.ndarray:
    arr = np.asarray(rgb, dtype=np.float32).copy()
    if arr.ndim != 3 or arr.shape[-1] != 3:
        return arr
    red = arr[..., 0]
    green = arr[..., 1]
    blue = arr[..., 2]
    target = (red + blue) / 2.0
    excess = np.maximum(green - target, 0.0)
    arr[..., 1] = green - excess * strength
    return arr


def _apply_mono(data: np.ndarray) -> np.ndarray:
    mono = np.asarray(data, dtype=np.float32)
    return np.stack([mono, mono, mono], axis=-1)


def _stretch_to_uint8(data: np.ndarray, stretch: str, black: float, white: float, gamma: float) -> np.ndarray:
    arr = np.asarray(data, dtype=np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        if arr.ndim == 3:
            return np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
        return np.zeros(arr.shape[:2], dtype=np.uint8)

    valid = arr[finite]
    lo = float(np.percentile(valid, black))
    hi = float(np.percentile(valid, white))
    if hi <= lo:
        hi = lo + 1.0

    norm = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
    stretch_mode = _normalize_stretch_mode(stretch)
    if stretch_mode == "linear":
        stretched = norm
    else:
        strength = 10.0 if stretch_mode == "arcsinh" else 8.0
        stretched = np.arcsinh(norm * strength) / np.arcsinh(strength)

    gamma_value = max(0.2, float(gamma))
    corrected = np.power(np.clip(stretched, 0.0, 1.0), 1.0 / gamma_value)
    return np.clip(corrected * 255.0, 0, 255).astype(np.uint8)


def _square_crop(image: Image.Image, size: int) -> Image.Image:
    width, height = image.size
    if width == height:
        return image.resize((size, size), Image.Resampling.LANCZOS)
    side = min(width, height)
    left = max(0, (width - side) // 2)
    top = max(0, (height - side) // 2)
    cropped = image.crop((left, top, left + side, top + side))
    return cropped.resize((size, size), Image.Resampling.LANCZOS)


def _resize_detail(image: Image.Image, max_width: int = 1600) -> Image.Image:
    width, height = image.size
    if width <= max_width:
        return image
    ratio = max_width / float(width)
    return image.resize((max_width, max(1, int(height * ratio))), Image.Resampling.LANCZOS)


def render_raw_file_fits_preview(
    raw_file: dict[str, Any],
    debayer: str | None,
    stretch: str | None,
    black: str | None,
    white: str | None,
    gamma: str | None,
    kind: str | None,
) -> tuple[bytes, str]:
    try:
        from astropy.io import fits  # type: ignore
    except Exception as exc:
        raise RuntimeError("astropy is required for FITS preview rendering") from exc

    path = _resolve_fits_path(raw_file)
    debayer_mode = _normalize_debayer_mode(debayer)
    stretch_mode = _normalize_stretch_mode(stretch)
    black_value = _parse_float(black, DEFAULT_BLACK, 0.0, 25.0)
    white_value = _parse_float(white, DEFAULT_WHITE, 75.0, 100.0)
    gamma_value = _parse_float(gamma, DEFAULT_GAMMA, 0.2, 4.0)
    render_kind = _normalize_render_kind(kind)

    with fits.open(path, memmap=False) as hdul:
        raw_data, header = _find_first_image_hdu(hdul)
        data = _prepare_array(raw_data)

    if data.ndim == 2:
        pattern = _detect_bayer_pattern(raw_file, header, debayer_mode)
        debayer_required = bool(raw_file.get("debayer_required")) or bool(raw_file.get("is_color_sensor")) or bool(str(raw_file.get("header_bayerpat") or header.get("BAYERPAT") or "").strip())
        if debayer_mode == "mono":
            prepared = _apply_mono(data)
        elif debayer_required or debayer_mode in {"rggb", "bggr", "grbg", "gbrg"}:
            prepared = _opencv_debayer(data, pattern)
            if prepared is None:
                prepared = _debayer_bayer(data, pattern)
            prepared = _background_neutralize(prepared)
            prepared = _reduce_green(prepared)
        else:
            prepared = _apply_mono(data)
        display = _stretch_to_uint8(prepared, stretch_mode, black_value, white_value, gamma_value)
    else:
        prepared = _background_neutralize(data)
        prepared = _reduce_green(prepared, strength=0.35)
        display = _stretch_to_uint8(prepared, stretch_mode, black_value, white_value, gamma_value)

    image = Image.fromarray(display)
    if render_kind == "thumb":
        image = _square_crop(image, 256)
    else:
        image = _resize_detail(image, 1600)

    buf = BytesIO()
    if _supports_webp():
        image.save(buf, format="WEBP", quality=88, method=6)
    else:
        image.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), _preview_mimetype()
