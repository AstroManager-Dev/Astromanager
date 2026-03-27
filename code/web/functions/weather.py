from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .common import CACHE_ROOT
from .observing import list_observing_sites, load_default_observing_site, load_observing_site

WEATHER_CACHE_ROOT = CACHE_ROOT / "web" / "weather"
WEATHER_CACHE_TTL = timedelta(minutes=30)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

GEOCODE_CACHE_TTL = timedelta(days=30)
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

CURRENT_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "cloud_cover",
    "wind_speed_10m",
    "precipitation",
    "weather_code",
    "is_day",
]

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "cloud_cover",
    "precipitation_probability",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]

DAILY_VARIABLES = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "precipitation_sum",
    "sunrise",
    "sunset",
]

WMO_LABELS = {
    0: ("Klar", "clear"),
    1: ("Meist klar", "clear"),
    2: ("Leicht bewölkt", "partly"),
    3: ("Bewölkt", "cloudy"),
    45: ("Nebel", "fog"),
    48: ("Raureifnebel", "fog"),
    51: ("Leichter Niesel", "rain"),
    53: ("Niesel", "rain"),
    55: ("Starker Niesel", "rain"),
    56: ("Gefrierender Niesel", "rain"),
    57: ("Starker gefrierender Niesel", "rain"),
    61: ("Leichter Regen", "rain"),
    63: ("Regen", "rain"),
    65: ("Starker Regen", "rain"),
    66: ("Gefrierender Regen", "rain"),
    67: ("Starker gefrierender Regen", "rain"),
    71: ("Leichter Schnee", "snow"),
    73: ("Schnee", "snow"),
    75: ("Starker Schnee", "snow"),
    77: ("Schneekörner", "snow"),
    80: ("Leichte Schauer", "rain"),
    81: ("Schauer", "rain"),
    82: ("Starke Schauer", "rain"),
    85: ("Leichte Schneeschauer", "snow"),
    86: ("Schneeschauer", "snow"),
    95: ("Gewitter", "storm"),
    96: ("Gewitter mit Hagel", "storm"),
    99: ("Starkes Gewitter", "storm"),
}


def _weather_meta_cache_path(site_id: int) -> Path:
    WEATHER_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return WEATHER_CACHE_ROOT / f"site_{site_id}_meta.json"


def _load_cached_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cached_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _extract_locality(address: dict[str, Any]) -> tuple[str, str]:
    city = str(
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
        or ""
    ).strip()
    district = str(
        address.get("suburb")
        or address.get("city_district")
        or address.get("quarter")
        or address.get("neighbourhood")
        or address.get("borough")
        or ""
    ).strip()
    if district and district.lower() == city.lower():
        district = ""
    return city, district


def _valid_timezone_name(value: Any) -> str:
    tz = str(value or "").strip()
    if not tz or "/" not in tz:
        return ""
    try:
        ZoneInfo(tz)
    except Exception:
        return ""
    return tz


def _format_local_timestamp(value: str | None, timezone_name: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return str(value)
    if dt.tzinfo is None and timezone_name:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:
            pass
    return dt.strftime("%d.%m.%Y %H:%M")


def _reverse_geocode_site(site: dict[str, Any]) -> dict[str, Any]:
    site_id = int(site.get("id") or 0)
    if site_id <= 0:
        return {}
    cache_path = _weather_meta_cache_path(site_id)
    cached = _load_cached_json(cache_path)
    if _cache_fresh(cached, ttl=GEOCODE_CACHE_TTL):
        return cached or {}

    params = {
        "lat": site.get("latitude_deg"),
        "lon": site.get("longitude_deg"),
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 14,
    }
    url = f"{NOMINATIM_REVERSE_URL}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "AstroManager/0.4 weather reverse geocode"})
    with urlopen(req, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    address = data.get("address") or {}
    city, district = _extract_locality(address)
    payload = {
        "city": city,
        "district": district,
        "display_name": str(data.get("display_name") or "").strip(),
        "_fetched_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    _save_cached_json(cache_path, payload)
    return payload


def _site_display_context(site: dict[str, Any] | None) -> dict[str, Any]:
    if not site:
        return {}
    geo: dict[str, Any] = {}
    try:
        geo = _reverse_geocode_site(site)
    except Exception:
        geo = {}
    city = str(geo.get("city") or "").strip()
    district = str(geo.get("district") or "").strip()
    locality_line = " · ".join([part for part in [city, district] if part])
    timezone_name = _valid_timezone_name(site.get("timezone_name"))
    detail_parts = [
        f"{float(site.get('latitude_deg') or 0.0):.5f} / {float(site.get('longitude_deg') or 0.0):.5f}",
        f"{float(site.get('elevation_m') or 0.0):.1f} m" if site.get("elevation_m") is not None else None,
    ]
    return {
        "site_name": str(site.get("name") or "Standort").strip(),
        "is_default": bool(site.get("is_default")),
        "city": city,
        "district": district,
        "locality_line": locality_line,
        "detail_line": " · ".join([part for part in detail_parts if part]),
        "timezone_name": timezone_name,
        "display_name": str(geo.get("display_name") or "").strip(),
    }


def _weather_cache_path(site_id: int) -> Path:
    WEATHER_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return WEATHER_CACHE_ROOT / f"site_{site_id}.json"


def _load_cached_forecast(site_id: int) -> dict[str, Any] | None:
    path = _weather_cache_path(site_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cached_forecast(site_id: int, payload: dict[str, Any]) -> None:
    path = _weather_cache_path(site_id)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _cache_fresh(payload: dict[str, Any] | None, *, ttl: timedelta = WEATHER_CACHE_TTL) -> bool:
    if not payload:
        return False
    fetched_at = str(payload.get("_fetched_at") or "").strip()
    if not fetched_at:
        return False
    try:
        ts = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False
    return datetime.utcnow() - ts < ttl


def _fetch_forecast(site: dict[str, Any]) -> dict[str, Any]:
    params = {
        "latitude": site["latitude_deg"],
        "longitude": site["longitude_deg"],
        "current": ",".join(CURRENT_VARIABLES),
        "hourly": ",".join(HOURLY_VARIABLES),
        "daily": ",".join(DAILY_VARIABLES),
        "forecast_days": 7,
        "timezone": ((site.get("timezone_name") or "") if "/" in str(site.get("timezone_name") or "") else "auto"),
        "wind_speed_unit": "kmh",
    }
    if site.get("elevation_m") is not None:
        params["elevation"] = site["elevation_m"]
    url = f"{OPEN_METEO_BASE_URL}?{urlencode(params)}"
    with urlopen(url, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))
    data["_fetched_at"] = datetime.utcnow().isoformat(timespec="seconds")
    data["_source_url"] = url
    return data


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _wmo_label(code: Any) -> tuple[str, str]:
    try:
        return WMO_LABELS.get(int(code), ("Unbekannt", "unknown"))
    except (TypeError, ValueError):
        return ("Unbekannt", "unknown")


def _build_current_block(payload: dict[str, Any]) -> dict[str, Any]:
    current = payload.get("current") or {}
    weather_label, weather_kind = _wmo_label(current.get("weather_code"))
    return {
        "temperature": _safe_float(current.get("temperature_2m")),
        "humidity": _safe_float(current.get("relative_humidity_2m")),
        "cloud_cover": _safe_float(current.get("cloud_cover")),
        "wind_speed": _safe_float(current.get("wind_speed_10m")),
        "precipitation": _safe_float(current.get("precipitation")),
        "is_day": bool(int(current.get("is_day") or 0)),
        "weather_label": weather_label,
        "weather_kind": weather_kind,
        "time": current.get("time"),
    }


def _hourly_rows(payload: dict[str, Any], *, limit: int = 12) -> list[dict[str, Any]]:
    hourly = payload.get("hourly") or {}
    times = list(hourly.get("time") or [])
    if not times:
        return []

    current_time_value = str((payload.get("current") or {}).get("time") or "").strip()
    start_idx = 0
    if current_time_value:
        for idx, value in enumerate(times):
            if value >= current_time_value:
                start_idx = idx
                break

    rows: list[dict[str, Any]] = []
    end_idx = min(start_idx + limit, len(times))
    for idx in range(start_idx, end_idx):
        time_value = times[idx]
        weather_label, weather_kind = _wmo_label((hourly.get("weather_code") or [None])[idx] if idx < len(hourly.get("weather_code") or []) else None)
        rows.append(
            {
                "time": time_value,
                "hour_label": datetime.fromisoformat(time_value).strftime("%H:%M") if time_value else "—",
                "temperature": _safe_float((hourly.get("temperature_2m") or [None])[idx] if idx < len(hourly.get("temperature_2m") or []) else None),
                "cloud_cover": _safe_float((hourly.get("cloud_cover") or [None])[idx] if idx < len(hourly.get("cloud_cover") or []) else None),
                "humidity": _safe_float((hourly.get("relative_humidity_2m") or [None])[idx] if idx < len(hourly.get("relative_humidity_2m") or []) else None),
                "wind_speed": _safe_float((hourly.get("wind_speed_10m") or [None])[idx] if idx < len(hourly.get("wind_speed_10m") or []) else None),
                "precipitation_probability": _safe_float((hourly.get("precipitation_probability") or [None])[idx] if idx < len(hourly.get("precipitation_probability") or []) else None),
                "precipitation": _safe_float((hourly.get("precipitation") or [None])[idx] if idx < len(hourly.get("precipitation") or []) else None),
                "weather_label": weather_label,
                "weather_kind": weather_kind,
            }
        )
    return rows


def _score_night(cloud_avg: float | None, humidity_avg: float | None, wind_max: float | None, precip_prob_max: float | None) -> tuple[str, str, int]:
    score = 100
    if cloud_avg is not None:
        score -= int(cloud_avg * 0.7)
    if humidity_avg is not None:
        score -= int(max(humidity_avg - 55, 0) * 0.35)
    if wind_max is not None:
        score -= int(max(wind_max - 10, 0) * 1.8)
    if precip_prob_max is not None:
        score -= int(precip_prob_max * 0.25)
    score = max(0, min(100, score))
    if score >= 75:
        return "Gut", "good", score
    if score >= 50:
        return "Mittel", "okay", score
    if score >= 30:
        return "Schwach", "weak", score
    return "Schlecht", "bad", score


def _build_night_rows(payload: dict[str, Any], *, limit: int = 5) -> list[dict[str, Any]]:
    hourly = payload.get("hourly") or {}
    times = list(hourly.get("time") or [])
    if not times:
        return []

    current_time_value = str((payload.get("current") or {}).get("time") or "").strip()
    current_dt = datetime.fromisoformat(current_time_value) if current_time_value else None
    min_bucket_date = None
    if current_dt is not None:
        min_bucket_date = current_dt.date() - timedelta(days=1) if current_dt.hour < 6 else current_dt.date()

    buckets: dict[str, list[dict[str, Any]]] = {}
    for idx, time_value in enumerate(times):
        if not time_value:
            continue
        dt = datetime.fromisoformat(time_value)
        if 6 <= dt.hour < 20:
            continue
        bucket_date = dt.date()
        if dt.hour < 6:
            bucket_date = bucket_date - timedelta(days=1)
        bucket_key = bucket_date.isoformat()
        buckets.setdefault(bucket_key, []).append(
            {
                "dt": dt,
                "cloud": _safe_float((hourly.get("cloud_cover") or [None])[idx] if idx < len(hourly.get("cloud_cover") or []) else None),
                "humidity": _safe_float((hourly.get("relative_humidity_2m") or [None])[idx] if idx < len(hourly.get("relative_humidity_2m") or []) else None),
                "wind": _safe_float((hourly.get("wind_speed_10m") or [None])[idx] if idx < len(hourly.get("wind_speed_10m") or []) else None),
                "precip_prob": _safe_float((hourly.get("precipitation_probability") or [None])[idx] if idx < len(hourly.get("precipitation_probability") or []) else None),
                "weather_code": (hourly.get("weather_code") or [None])[idx] if idx < len(hourly.get("weather_code") or []) else None,
            }
        )

    rows: list[dict[str, Any]] = []
    bucket_keys = sorted(buckets.keys())
    if min_bucket_date is not None:
        bucket_keys = [key for key in bucket_keys if datetime.fromisoformat(key).date() >= min_bucket_date]
    for bucket_key in bucket_keys[:limit]:
        values = buckets[bucket_key]
        cloud_vals = [x["cloud"] for x in values if x["cloud"] is not None]
        humidity_vals = [x["humidity"] for x in values if x["humidity"] is not None]
        wind_vals = [x["wind"] for x in values if x["wind"] is not None]
        precip_vals = [x["precip_prob"] for x in values if x["precip_prob"] is not None]
        weather_codes = [x["weather_code"] for x in values if x["weather_code"] is not None]

        cloud_avg = round(mean(cloud_vals), 1) if cloud_vals else None
        humidity_avg = round(mean(humidity_vals), 1) if humidity_vals else None
        wind_max = round(max(wind_vals), 1) if wind_vals else None
        precip_prob_max = round(max(precip_vals), 1) if precip_vals else None
        main_code = weather_codes[len(weather_codes)//2] if weather_codes else None
        weather_label, weather_kind = _wmo_label(main_code)
        quality_label, quality_kind, quality_score = _score_night(cloud_avg, humidity_avg, wind_max, precip_prob_max)

        bucket_date = datetime.fromisoformat(bucket_key)
        rows.append(
            {
                "date": bucket_key,
                "label": bucket_date.strftime("%d.%m.%Y"),
                "cloud_avg": cloud_avg,
                "humidity_avg": humidity_avg,
                "wind_max": wind_max,
                "precip_prob_max": precip_prob_max,
                "weather_label": weather_label,
                "weather_kind": weather_kind,
                "quality_label": quality_label,
                "quality_kind": quality_kind,
                "quality_score": quality_score,
            }
        )
    return rows


def _daily_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    daily = payload.get("daily") or {}
    times = list(daily.get("time") or [])
    rows: list[dict[str, Any]] = []
    for idx, time_value in enumerate(times):
        weather_label, weather_kind = _wmo_label((daily.get("weather_code") or [None])[idx] if idx < len(daily.get("weather_code") or []) else None)
        dt = datetime.fromisoformat(time_value) if time_value else None
        rows.append(
            {
                "date": time_value,
                "label": dt.strftime("%a %d.%m.") if dt else "—",
                "temp_min": _safe_float((daily.get("temperature_2m_min") or [None])[idx] if idx < len(daily.get("temperature_2m_min") or []) else None),
                "temp_max": _safe_float((daily.get("temperature_2m_max") or [None])[idx] if idx < len(daily.get("temperature_2m_max") or []) else None),
                "precipitation_probability_max": _safe_float((daily.get("precipitation_probability_max") or [None])[idx] if idx < len(daily.get("precipitation_probability_max") or []) else None),
                "precipitation_sum": _safe_float((daily.get("precipitation_sum") or [None])[idx] if idx < len(daily.get("precipitation_sum") or []) else None),
                "sunrise": (daily.get("sunrise") or [None])[idx] if idx < len(daily.get("sunrise") or []) else None,
                "sunset": (daily.get("sunset") or [None])[idx] if idx < len(daily.get("sunset") or []) else None,
                "weather_label": weather_label,
                "weather_kind": weather_kind,
            }
        )
    return rows


def build_weather_context(selected_site_id: int | None) -> dict[str, Any]:
    sites = list_observing_sites()
    default_site = load_default_observing_site()
    selected_site = load_observing_site(selected_site_id) if selected_site_id else None
    if selected_site is None:
        selected_site = default_site or (sites[0] if sites else None)

    context: dict[str, Any] = {
        "weather_available_sites": sites,
        "weather_selected_site": selected_site,
        "weather_selected_site_id": int(selected_site["id"]) if selected_site and selected_site.get("id") is not None else None,
        "weather_site_display": _site_display_context(selected_site) if selected_site else {},
        "weather_current": None,
        "weather_hourly_rows": [],
        "weather_night_rows": [],
        "weather_featured_night": None,
        "weather_upcoming_nights": [],
        "weather_daily_rows": [],
        "weather_error": "",
        "weather_updated_at": "",
        "weather_updated_at_label": "",
        "weather_source_url": "",
    }
    if not selected_site:
        context["weather_error"] = "Noch kein Standort vorhanden. Bitte zuerst unter Einstellungen → Standorte einen Beobachtungsort anlegen."
        return context

    cached = _load_cached_forecast(int(selected_site["id"]))
    payload: dict[str, Any] | None = cached if _cache_fresh(cached) else None
    if payload is None:
        try:
            payload = _fetch_forecast(selected_site)
            _save_cached_forecast(int(selected_site["id"]), payload)
        except Exception:
            if cached:
                payload = cached
            else:
                context["weather_error"] = "Forecast konnte momentan nicht geladen werden."
                return context

    context["weather_current"] = _build_current_block(payload)
    context["weather_hourly_rows"] = _hourly_rows(payload)
    context["weather_night_rows"] = _build_night_rows(payload)
    context["weather_featured_night"] = context["weather_night_rows"][0] if context["weather_night_rows"] else None
    context["weather_upcoming_nights"] = context["weather_night_rows"][1:] if len(context["weather_night_rows"]) > 1 else []
    context["weather_daily_rows"] = _daily_rows(payload)
    context["weather_updated_at"] = payload.get("_fetched_at") or ""
    timezone_name = _valid_timezone_name((payload.get("timezone") or selected_site.get("timezone_name") if selected_site else ""))
    current_time_value = str((payload.get("current") or {}).get("time") or "").strip()
    label_source = current_time_value or context["weather_updated_at"]
    context["weather_updated_at_label"] = _format_local_timestamp(label_source, timezone_name)
    context["weather_source_url"] = payload.get("_source_url") or ""
    return context
