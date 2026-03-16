from typing import Any


def _format_session_datetime_label(value: Any) -> str:
    raw = str(value or '').strip()
    if not raw:
        return '—'
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})[- T](\d{2})-(\d{2})(?:-(\d{2}))?', raw)
    if match:
        year, month, day, hour, minute, _second = match.groups()
        return f'{day}.{month}.{year} · {hour}:{minute}'
    return raw


def _format_session_group_label(value: str) -> str:
    raw = str(value or '').strip()
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', raw)
    if match:
        year, month, day = match.groups()
        return f'{day}.{month}.{year}'
    return raw or 'Unbekannt'


def _format_exposure_duration_label(total_seconds: Any) -> str:
    try:
        seconds = int(round(float(total_seconds or 0)))
    except Exception:
        return '—'
    if seconds <= 0:
        return '—'
    total_minutes = max(1, int(round(seconds / 60.0)))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours:
        return f'{hours}h {minutes:02d}m'
    return f'{total_minutes}m'


def _format_session_month_label(value: str) -> str:
    raw = str(value or '').strip()
    match = re.match(r'^(\d{4})-(\d{2})$', raw)
    if not match:
        return raw or 'Unbekannt'
    year, month = match.groups()
    names = {
        '01': 'Januar', '02': 'Februar', '03': 'März', '04': 'April',
        '05': 'Mai', '06': 'Juni', '07': 'Juli', '08': 'August',
        '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Dezember',
    }
    return f"{names.get(month, month)} {year}"
