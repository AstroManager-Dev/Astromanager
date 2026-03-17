from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _normalize_view_mode(value: str | None, is_fits: bool) -> str:
    mode = (value or "file").strip().lower()
    if mode == "fits" and is_fits:
        return "fits"
    return "file"


def _normalize_debayer_mode(value: str | None) -> str:
    mode = (value or "auto").strip().lower()
    return mode if mode in {"auto", "mono"} else "auto"


def _normalize_render_kind(value: str | None) -> str:
    kind = (value or "detail").strip().lower()
    return kind if kind in {"detail", "thumb"} else "detail"


def enrich_raw_file_viewer_context(
    raw_file: dict[str, Any],
    view: str | None = None,
    debayer: str | None = None,
    stretch: str | None = None,
    black: str | None = None,
    white: str | None = None,
    gamma: str | None = None,
) -> dict[str, Any]:
    item = dict(raw_file)
    is_fits = bool(item.get("is_fits"))
    view_mode = _normalize_view_mode(view, is_fits)
    debayer_mode = _normalize_debayer_mode(debayer)
    stretch_mode = (stretch or "auto").strip().lower() or "auto"
    black_value = str(black).strip() if black is not None and str(black).strip() else "0.500"
    white_value = str(white).strip() if white is not None and str(white).strip() else "99.500"
    gamma_value = str(gamma).strip() if gamma is not None and str(gamma).strip() else "1.000"
    raw_file_id = int(item.get("id") or 0)

    viewer_query = (
        f"debayer={debayer_mode}&stretch={stretch_mode}"
        f"&black={black_value}&white={white_value}&gamma={gamma_value}"
    )

    item.update(
        {
            "view_mode": view_mode,
            "debayer_mode": debayer_mode,
            "stretch_mode": stretch_mode,
            "black_value": black_value,
            "white_value": white_value,
            "gamma_value": gamma_value,
            "view_file_href": f"/raw-files/{raw_file_id}?view=file",
            "view_fits_href": f"/raw-files/{raw_file_id}?view=fits&{viewer_query}",
            "debayer_auto_href": f"/raw-files/{raw_file_id}?view=fits&debayer=auto&stretch={stretch_mode}&black={black_value}&white={white_value}&gamma={gamma_value}",
            "debayer_mono_href": f"/raw-files/{raw_file_id}?view=fits&debayer=mono&stretch={stretch_mode}&black={black_value}&white={white_value}&gamma={gamma_value}",
            "fits_preview_url": f"/media/raw-file-fits-preview/{raw_file_id}.png?{viewer_query}&kind=detail",
            "fits_thumb_url": f"/media/raw-file-fits-preview/{raw_file_id}.png?debayer={debayer_mode}&kind=thumb",
            "fits_viewer_available": is_fits,
            "fits_viewer_note": "Serverseitige Vorschau mit Stretch- und Debayer-Kompatibilität.",
        }
    )
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
    else:  # RGGB default
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


def _stretch_to_uint8(data: np.ndarray) -> np.ndarray:
    arr = np.asarray(data, dtype=np.float32)
    finite = np.isfinite(arr)
    if not finite.any():
        if arr.ndim == 3:
            return np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
        return np.zeros(arr.shape[:2], dtype=np.uint8)
    valid = arr[finite]
    lo = float(np.percentile(valid, 0.5))
    hi = float(np.percentile(valid, 99.5))
    if hi <= lo:
        hi = lo + 1.0
    norm = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
    stretched = np.arcsinh(norm * 8.0) / np.arcsinh(8.0)
    return np.clip(stretched * 255.0, 0, 255).astype(np.uint8)


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


def render_raw_file_fits_preview(raw_file: dict[str, Any], debayer: str | None, kind: str | None) -> bytes:
    try:
        from astropy.io import fits  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("astropy is required for FITS preview rendering") from exc

    path = _resolve_fits_path(raw_file)
    debayer_mode = _normalize_debayer_mode(debayer)
    render_kind = _normalize_render_kind(kind)

    with fits.open(path, memmap=False) as hdul:
        raw_data, header = _find_first_image_hdu(hdul)
        data = _prepare_array(raw_data)

    if data.ndim == 2:
        pattern = str(raw_file.get("header_bayerpat") or header.get("BAYERPAT") or "").strip().upper()
        xoff = int(raw_file.get("header_xbayroff") or header.get("XBAYROFF") or 0)
        yoff = int(raw_file.get("header_ybayroff") or header.get("YBAYROFF") or 0)
        debayer_required = bool(raw_file.get("debayer_required")) or bool(raw_file.get("is_color_sensor")) or bool(pattern)
        if debayer_mode == "auto" and debayer_required:
            rgb = _debayer_bayer(data, pattern or "RGGB", xoff=xoff, yoff=yoff)
            display = _stretch_to_uint8(rgb)
        else:
            display = _stretch_to_uint8(data)
    else:
        display = _stretch_to_uint8(data)

    image = Image.fromarray(display)
    if render_kind == "thumb":
        image = _square_crop(image, 256)
    else:
        image = _resize_detail(image, 1600)

    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
