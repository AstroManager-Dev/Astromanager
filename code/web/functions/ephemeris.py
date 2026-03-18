from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import swisseph as swe

from .database import db_conn, db_table_exists, row_to_dict
from .observing import load_default_observing_site, load_observing_site, list_observing_sites

_SYNODIC_MONTH_DAYS = 29.530588853


def _parse_session_datetime(value: Any) -> datetime | None:
    text = str(value or '').strip()
    if not text:
        return None
    normalized = text.replace('T', ' ')
    for candidate in (normalized, normalized.replace('Z', '+00:00')):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y-%m-%d-%H-%M-%S-%f', '%Y-%m-%d-%H-%M-%S'):
        try:
            dt = datetime.strptime(normalized, fmt).replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _datetime_to_jd(dt: datetime) -> float:
    hour = dt.hour + dt.minute / 60.0 + (dt.second + dt.microsecond / 1_000_000.0) / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)


def _jd_to_iso_utc(jd: float | None) -> str:
    if jd in (None, 0, ''):
        return ''
    year, month, day, hour = swe.revjul(float(jd))
    base = datetime(year, month, day, tzinfo=timezone.utc)
    seconds = int(round(float(hour) * 3600))
    final = base + timedelta(seconds=seconds)
    return final.replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _format_deg(value: Any, digits: int = 1) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value):.{digits}f}°'


def _format_distance_km(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value):,.0f} km'.replace(',', '.')


def _format_distance_au(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value):.6f} AU'


def _format_percent(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value) * 100.0:.1f} %'


def _format_arcmin(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value):.2f}′'


def _format_days(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return '—'
    return f'{float(value):.1f} d'


def _format_timestamp(value: Any) -> str:
    text = str(value or '').strip()
    if not text:
        return '—'
    return text.replace('T', ' ').replace('Z', ' UTC')


def _azimuth_to_north(az_south_west: float) -> float:
    return (float(az_south_west) + 180.0) % 360.0


def _phase_name(delta_lon_deg: float) -> str:
    value = delta_lon_deg % 360.0
    names = [
        (22.5, 'Neumond'),
        (67.5, 'Zunehmende Sichel'),
        (112.5, 'Erstes Viertel'),
        (157.5, 'Zunehmender Mond'),
        (202.5, 'Vollmond'),
        (247.5, 'Abnehmender Mond'),
        (292.5, 'Letztes Viertel'),
        (337.5, 'Abnehmende Sichel'),
        (360.0, 'Neumond'),
    ]
    for limit, label in names:
        if value < limit:
            return label
    return 'Mondphase'


def _airmass_from_altitude(alt_deg: float | None) -> float | None:
    if alt_deg is None:
        return None
    zenith = 90.0 - float(alt_deg)
    if zenith >= 90.0:
        return None
    cosz = math.cos(math.radians(zenith))
    if cosz <= 0:
        return None
    return 1.0 / (cosz + 0.50572 * ((96.07995 - zenith) ** -1.6364))


def _event_time(jd: float, body: int, rsmi: int, geopos: tuple[float, float, float]) -> str:
    try:
        res, tret = swe.rise_trans(jd, body, rsmi, geopos, 0.0, 10.0, swe.FLG_SWIEPH)
        if int(res) != 0:
            return ''
        return _jd_to_iso_utc(tret[0])
    except Exception:
        return ''


def _compute_observer_values(jd: float, ra_deg: float, dec_deg: float, geopos: tuple[float, float, float]) -> tuple[float | None, float | None]:
    try:
        az_s, true_alt, _ = swe.azalt(jd, swe.EQU2HOR, geopos, 0.0, 10.0, (ra_deg, dec_deg, 1.0))
        return float(true_alt), _azimuth_to_north(float(az_s))
    except Exception:
        return None, None


def _site_context(site_id: int | None) -> tuple[dict[str, Any] | None, str]:
    if site_id:
        site = load_observing_site(int(site_id))
        if site:
            return site, 'topocentric_site'
    site = load_default_observing_site()
    if site:
        return site, 'topocentric_default_site'
    return None, 'geocentric_fallback'


def _upsert(table: str, session_id: int, values: dict[str, Any]) -> None:
    conn = db_conn()
    try:
        if not db_table_exists(conn, table):
            return
        payload = {'session_id': session_id, **values}
        columns = list(payload.keys())
        placeholders = ', '.join(['?'] * len(columns))
        update_cols = [col for col in columns if col != 'session_id']
        update_sql = ', '.join([f"{col} = excluded.{col}" for col in update_cols])
        conn.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT(session_id) DO UPDATE SET {update_sql}",
            tuple(payload[col] for col in columns),
        )
        conn.commit()
    finally:
        conn.close()


def _load_saved(table: str, session_id: int) -> dict[str, Any] | None:
    conn = db_conn()
    try:
        if not db_table_exists(conn, table):
            return None
        row = conn.execute(f'SELECT * FROM {table} WHERE session_id = ? LIMIT 1', (session_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def compute_session_moon_ephemeris(session_row: dict[str, Any]) -> dict[str, Any] | None:
    dt = _parse_session_datetime(session_row.get('session_datetime'))
    if dt is None:
        return None
    jd = _datetime_to_jd(dt)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    moon, _ = swe.calc_ut(jd, swe.MOON, flags)
    moon_eq, _ = swe.calc_ut(jd, swe.MOON, flags | swe.FLG_EQUATORIAL)
    sun, _ = swe.calc_ut(jd, swe.SUN, flags)
    pheno = swe.pheno_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    delta_lon = (float(moon[0]) - float(sun[0])) % 360.0
    age_days = _SYNODIC_MONTH_DAYS * delta_lon / 360.0
    site, computation_mode = _site_context(session_row.get('observing_site_id'))
    geopos = None
    alt_deg = az_deg = None
    rise_utc = set_utc = transit_utc = ''
    if site:
        geopos = (float(site.get('longitude_deg') or 0.0), float(site.get('latitude_deg') or 0.0), float(site.get('elevation_m') or 0.0))
        alt_deg, az_deg = _compute_observer_values(jd, float(moon_eq[0]), float(moon_eq[1]), geopos)
        rise_utc = _event_time(jd - 0.75, swe.MOON, swe.CALC_RISE, geopos)
        set_utc = _event_time(jd - 0.75, swe.MOON, swe.CALC_SET, geopos)
        transit_utc = _event_time(jd - 0.75, swe.MOON, swe.CALC_MTRANSIT, geopos)
    values = {
        'site_id': int(site['id']) if site else None,
        'computed_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'ephemeris_source': 'swisseph',
        'observation_time_utc': dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'computation_mode': computation_mode,
        'moon_phase_name': _phase_name(delta_lon),
        'illumination_fraction': float(pheno[1]),
        'moon_age_days': float(age_days),
        'distance_km': float(moon[2]) * swe.AUNIT_TO_KM,
        'angular_diameter_arcmin': float(pheno[3]),
        'libration_lon_deg': None,
        'libration_lat_deg': None,
        'position_angle_deg': None,
        'colongitude_deg': (90.0 - float(moon[0]) + float(sun[0])) % 360.0,
        'ra_deg': float(moon_eq[0]),
        'dec_deg': float(moon_eq[1]),
        'ecliptic_lon_deg': float(moon[0]),
        'ecliptic_lat_deg': float(moon[1]),
        'alt_deg': alt_deg,
        'az_deg': az_deg,
        'rise_utc': rise_utc,
        'set_utc': set_utc,
        'transit_utc': transit_utc,
    }
    _upsert('session_moon_ephemeris', int(session_row['id']), values)
    return _load_saved('session_moon_ephemeris', int(session_row['id']))


def compute_session_sun_ephemeris(session_row: dict[str, Any]) -> dict[str, Any] | None:
    dt = _parse_session_datetime(session_row.get('session_datetime'))
    if dt is None:
        return None
    jd = _datetime_to_jd(dt)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    sun, _ = swe.calc_ut(jd, swe.SUN, flags)
    sun_eq, _ = swe.calc_ut(jd, swe.SUN, flags | swe.FLG_EQUATORIAL)
    pheno = swe.pheno_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    site, computation_mode = _site_context(session_row.get('observing_site_id'))
    geopos = None
    alt_deg = az_deg = None
    sunrise_utc = sunset_utc = transit_utc = ''
    airmass = None
    if site:
        geopos = (float(site.get('longitude_deg') or 0.0), float(site.get('latitude_deg') or 0.0), float(site.get('elevation_m') or 0.0))
        alt_deg, az_deg = _compute_observer_values(jd, float(sun_eq[0]), float(sun_eq[1]), geopos)
        sunrise_utc = _event_time(jd - 0.75, swe.SUN, swe.CALC_RISE, geopos)
        sunset_utc = _event_time(jd - 0.75, swe.SUN, swe.CALC_SET, geopos)
        transit_utc = _event_time(jd - 0.75, swe.SUN, swe.CALC_MTRANSIT, geopos)
        airmass = _airmass_from_altitude(alt_deg)
    values = {
        'site_id': int(site['id']) if site else None,
        'computed_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'ephemeris_source': 'swisseph',
        'observation_time_utc': dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'computation_mode': computation_mode,
        'ra_deg': float(sun_eq[0]),
        'dec_deg': float(sun_eq[1]),
        'distance_au': float(sun[2]),
        'distance_km': float(sun[2]) * swe.AUNIT_TO_KM,
        'angular_diameter_arcmin': float(pheno[3]),
        'p_angle_deg': None,
        'b0_deg': None,
        'l0_deg': float(sun[0]),
        'carrington_rotation': None,
        'central_meridian_lon_deg': None,
        'alt_deg': alt_deg,
        'az_deg': az_deg,
        'airmass': airmass,
        'sunrise_utc': sunrise_utc,
        'sunset_utc': sunset_utc,
        'transit_utc': transit_utc,
    }
    _upsert('session_sun_ephemeris', int(session_row['id']), values)
    return _load_saved('session_sun_ephemeris', int(session_row['id']))


def load_session_ephemeris_context(session_row: dict[str, Any]) -> dict[str, Any]:
    category = str(session_row.get('category') or '').strip().lower()
    assigned_site = load_observing_site(int(session_row.get('observing_site_id'))) if session_row.get('observing_site_id') else None
    default_site = load_default_observing_site()
    effective_site = assigned_site or default_site
    context: dict[str, Any] = {
        'available_sites': list_observing_sites(),
        'assigned_site': assigned_site,
        'default_site': default_site,
        'effective_site': effective_site,
        'effective_site_label': str(effective_site.get('name') or '') if effective_site else 'Kein Standort',
        'site_assignment_mode': 'assigned' if assigned_site else ('default' if default_site else 'none'),
        'moon_info_items': [],
        'sun_info_items': [],
        'moon_info_ready': False,
        'sun_info_ready': False,
    }
    if category == 'moon':
        item = compute_session_moon_ephemeris(session_row)
        if item:
            context['moon_info_ready'] = True
            context['moon_info_source_label'] = 'standortbasiert' if str(item.get('computation_mode') or '').startswith('topocentric') else 'geozentrisch'
            context['moon_info_items'] = [
                {'label': 'Phase', 'value': str(item.get('moon_phase_name') or '—')},
                {'label': 'Beleuchtung', 'value': _format_percent(item.get('illumination_fraction'))},
                {'label': 'Mondalter', 'value': _format_days(item.get('moon_age_days'))},
                {'label': 'Höhe', 'value': _format_deg(item.get('alt_deg'))},
                {'label': 'Azimut', 'value': _format_deg(item.get('az_deg'))},
                {'label': 'Distanz', 'value': _format_distance_km(item.get('distance_km'))},
                {'label': 'Scheibendurchmesser', 'value': _format_arcmin(item.get('angular_diameter_arcmin'))},
                {'label': 'Colongitude', 'value': _format_deg(item.get('colongitude_deg'))},
                {'label': 'RA', 'value': _format_deg(item.get('ra_deg'), 2)},
                {'label': 'DEC', 'value': _format_deg(item.get('dec_deg'), 2)},
                {'label': 'Mondaufgang', 'value': _format_timestamp(item.get('rise_utc'))},
                {'label': 'Monduntergang', 'value': _format_timestamp(item.get('set_utc'))},
                {'label': 'Transit', 'value': _format_timestamp(item.get('transit_utc'))},
            ]
    elif category == 'sun':
        item = compute_session_sun_ephemeris(session_row)
        if item:
            context['sun_info_ready'] = True
            context['sun_info_source_label'] = 'standortbasiert' if str(item.get('computation_mode') or '').startswith('topocentric') else 'geozentrisch'
            context['sun_info_items'] = [
                {'label': 'Höhe', 'value': _format_deg(item.get('alt_deg'))},
                {'label': 'Azimut', 'value': _format_deg(item.get('az_deg'))},
                {'label': 'Airmass', 'value': f"{float(item['airmass']):.2f}" if isinstance(item.get('airmass'), (int, float)) else '—'},
                {'label': 'Distanz', 'value': _format_distance_au(item.get('distance_au'))},
                {'label': 'Distanz km', 'value': _format_distance_km(item.get('distance_km'))},
                {'label': 'Scheibendurchmesser', 'value': _format_arcmin(item.get('angular_diameter_arcmin'))},
                {'label': 'RA', 'value': _format_deg(item.get('ra_deg'), 2)},
                {'label': 'DEC', 'value': _format_deg(item.get('dec_deg'), 2)},
                {'label': 'Sonnenaufgang', 'value': _format_timestamp(item.get('sunrise_utc'))},
                {'label': 'Sonnenuntergang', 'value': _format_timestamp(item.get('sunset_utc'))},
                {'label': 'Transit', 'value': _format_timestamp(item.get('transit_utc'))},
            ]
    return context
