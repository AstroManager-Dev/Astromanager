from __future__ import annotations

from typing import Any


def _display_value(value: Any, fallback: str = "—") -> str:
    if value in (None, ""):
        return fallback
    return str(value)


def _items_to_map(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        if not label:
            continue
        result[label] = item.get("value")
    return result


def _build_moon_card(session_row: dict[str, Any]) -> dict[str, Any]:
    moon_map = _items_to_map(session_row.get("moon_info_items"))
    return {
        "title": "Mond-Info",
        "template": "moon",
        "items": [
            {"label": "Phase", "value": _display_value(moon_map.get("Phase"))},
            {"label": "Mondalter", "value": _display_value(moon_map.get("Mondalter"))},
            {"label": "Beleuchtung", "value": _display_value(moon_map.get("Beleuchtung"))},
            {"label": "Distanz", "value": _display_value(moon_map.get("Distanz"))},
        ],
    }


def _build_sun_card(session_row: dict[str, Any]) -> dict[str, Any]:
    sun_map = _items_to_map(session_row.get("sun_info_items"))
    return {
        "title": "Sonnen-Info",
        "template": "sun",
        "items": [
            {"label": "Höhe", "value": _display_value(sun_map.get("Höhe"))},
            {"label": "Azimut", "value": _display_value(sun_map.get("Azimut"))},
            {"label": "Airmass", "value": _display_value(sun_map.get("Airmass"))},
            {"label": "Distanz", "value": _display_value(sun_map.get("Distanz km") or sun_map.get("Distanz"))},
        ],
    }


def _build_deepsky_card(session_row: dict[str, Any]) -> dict[str, Any]:
    frame_count = session_row.get("light_frames_count") or session_row.get("frame_count")
    return {
        "title": "Deep-Sky-Info",
        "template": "deepsky",
        "items": [
            {"label": "Target", "value": _display_value(session_row.get("display_target_name"))},
            {"label": "Frames", "value": _display_value(frame_count)},
            {"label": "Filter", "value": _display_value(session_row.get("filter_set"))},
            {"label": "Status", "value": _display_value(session_row.get("status"))},
        ],
    }


def _build_planet_card(session_row: dict[str, Any]) -> dict[str, Any]:
    frame_count = session_row.get("light_frames_count") or session_row.get("frame_count")
    return {
        "title": "Planeten-Info",
        "template": "planet",
        "items": [
            {"label": "Objekt", "value": _display_value(session_row.get("display_target_name"))},
            {"label": "Frames", "value": _display_value(frame_count)},
            {"label": "Filter", "value": _display_value(session_row.get("filter_set"))},
            {"label": "Status", "value": _display_value(session_row.get("status"))},
        ],
    }


def _build_object_card(session_row: dict[str, Any]) -> dict[str, Any] | None:
    category = str(session_row.get("category") or "").strip().lower()
    if category == "moon":
        return _build_moon_card(session_row)
    if category == "sun":
        return _build_sun_card(session_row)
    if category in {"planet", "solar_system"}:
        return _build_planet_card(session_row)
    if category == "deepsky":
        return _build_deepsky_card(session_row)
    return None


def build_session_object_infocard_context(session_row: dict[str, Any]) -> dict[str, Any]:
    card = _build_object_card(session_row)
    if not card:
        return {
            "object_info_card": None,
            "object_info_card_title": "",
            "object_info_card_template": "",
            "object_info_card_items": [],
        }
    return {
        "object_info_card": card,
        "object_info_card_title": card.get("title") or "",
        "object_info_card_template": card.get("template") or "",
        "object_info_card_items": card.get("items") or [],
    }
