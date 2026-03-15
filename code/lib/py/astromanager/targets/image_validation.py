from __future__ import annotations

import io
import urllib.request
from typing import Any

from .image_resolver_rules import (
    SKYVIEW_ALLOWED_IMAGE_CONTENT_TYPES,
    SKYVIEW_BLANK_SAMPLE_SIZE,
    SKYVIEW_BLANK_STDDEV_MAX,
    SKYVIEW_BLANK_UNIQUE_VALUES_MAX,
    SKYVIEW_ERROR_TEXT_TOKENS,
    SKYVIEW_MIN_IMAGE_BYTES,
)


def _decode_text(body: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return body.decode(encoding, errors="ignore")
        except Exception:
            continue
    return ""


def _validate_content_type(content_type: str) -> bool:
    content_type = (content_type or "").split(";")[0].strip().lower()
    return content_type in SKYVIEW_ALLOWED_IMAGE_CONTENT_TYPES


def _blank_image_metrics(body: bytes) -> dict[str, Any]:
    try:
        from PIL import Image, ImageStat  # type: ignore
    except Exception:
        return {"checked": False, "is_blank": False, "stddev": None, "unique_gray_values": None}

    try:
        image = Image.open(io.BytesIO(body)).convert("L")
        image.thumbnail(SKYVIEW_BLANK_SAMPLE_SIZE)
        stat = ImageStat.Stat(image)
        stddev = float(stat.stddev[0]) if stat.stddev else 0.0
        unique_values = len(set(image.getdata()))
        is_blank = stddev <= SKYVIEW_BLANK_STDDEV_MAX and unique_values <= SKYVIEW_BLANK_UNIQUE_VALUES_MAX
        return {"checked": True, "is_blank": is_blank, "stddev": stddev, "unique_gray_values": unique_values}
    except Exception:
        return {"checked": False, "is_blank": False, "stddev": None, "unique_gray_values": None}


def fetch_image_validation(url: str, timeout: float = 20.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AstroManager/0.4"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        status = getattr(response, "status", 200)
        content_type = response.headers.get("Content-Type", "")

    result = {
        "ok": True,
        "http_status": status,
        "content_type": content_type,
        "content_length": len(body),
        "error": "",
        "body_text": "",
        "is_blank": False,
        "pixel_stddev": None,
        "unique_gray_values": None,
    }

    if status >= 400:
        result["ok"] = False
        result["error"] = f"http_{status}"
        return result

    body_text = _decode_text(body).lower()
    result["body_text"] = body_text[:2000]

    if not _validate_content_type(content_type):
        if any(token in body_text for token in SKYVIEW_ERROR_TEXT_TOKENS):
            result["ok"] = False
            result["error"] = "no_data"
            return result
        result["ok"] = False
        result["error"] = f"unexpected_content_type:{(content_type or 'unknown').split(';')[0].strip().lower()}"
        return result

    if len(body) < SKYVIEW_MIN_IMAGE_BYTES:
        result["ok"] = False
        result["error"] = f"image_too_small:{len(body)}"
        return result

    metrics = _blank_image_metrics(body)
    result["is_blank"] = bool(metrics.get("is_blank"))
    result["pixel_stddev"] = metrics.get("stddev")
    result["unique_gray_values"] = metrics.get("unique_gray_values")
    if result["is_blank"]:
        result["ok"] = False
        result["error"] = "blank_image"
    return result
