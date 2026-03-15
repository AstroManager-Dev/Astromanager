#!/usr/bin/env python3
import csv
import io
import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from astromanager.targets.name_parser import normalize_catalog_name, lower_compact

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "25"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
SIMBAD_TAP_SYNC_URL = os.environ.get(
    "TARGET_RESOLVER_SIMBAD_TAP_SYNC_URL",
    "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
)

CONE_RADIUS_DEG = float(os.environ.get("TARGET_RESOLVER_SIMBAD_CONE_RADIUS_DEG", "0.2"))

BASIC_WANTED_COLUMNS = [
    "oid",
    "main_id",
    "otype",
    "otype_txt",
    "maintype",
    "ra",
    "dec",
    "pmra",
    "pmdec",
    "plx_value",
    "plx_err",
    "rvz_radvel",
    "rvz_redshift",
    "rvz_type",
    "rvz_error",
    "rvz_qual",
    "nbref",
]

IDENT_WANTED_COLUMNS = [
    "id",
]

FLUX_TABLE_CANDIDATES = ["allfluxes", "flux", "mesflux"]


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(value) -> str:
    return " ".join(str(value or "").strip().split())


def parse_float(value):
    try:
        if value is None:
            return None
        s = norm(value)
        if s == "":
            return None
        return float(s)
    except Exception:
        return None


def parse_int(value):
    try:
        if value is None:
            return None
        s = norm(value)
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def angular_sep_deg(ra1, dec1, ra2, dec2):
    if None in (ra1, dec1, ra2, dec2):
        return None
    ra1r = math.radians(float(ra1))
    dec1r = math.radians(float(dec1))
    ra2r = math.radians(float(ra2))
    dec2r = math.radians(float(dec2))
    cos_sep = (
        math.sin(dec1r) * math.sin(dec2r)
        + math.cos(dec1r) * math.cos(dec2r) * math.cos(ra1r - ra2r)
    )
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


def http_post_text(url: str, data: dict) -> str:
    payload = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain,text/csv,application/xml,text/xml,*/*",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def tap_query_csv(query: str) -> tuple[list[dict], str]:
    raw = http_post_text(
        SIMBAD_TAP_SYNC_URL,
        {
            "request": "doQuery",
            "lang": "adql",
            "format": "csv",
            "query": query,
        },
    )
    reader = csv.DictReader(io.StringIO(raw))
    rows = [dict(row) for row in reader]
    return rows, raw


def tap_query_votable(query: str) -> tuple[list[dict], str]:
    raw = http_post_text(
        SIMBAD_TAP_SYNC_URL,
        {
            "request": "doQuery",
            "lang": "adql",
            "format": "votable",
            "query": query,
        },
    )
    root = ET.fromstring(raw)
    ns = {"v": "http://www.ivoa.net/xml/VOTable/v1.3"}

    fields = []
    for field in root.findall(".//v:FIELD", ns):
        fields.append(field.attrib.get("name", ""))

    rows = []
    for tr in root.findall(".//v:TR", ns):
        vals = []
        for td in tr.findall("./v:TD", ns):
            vals.append(td.text or "")
        row = {}
        for idx, field_name in enumerate(fields):
            row[field_name] = vals[idx] if idx < len(vals) else ""
        rows.append(row)

    return rows, raw


def tap_query(query: str) -> tuple[list[dict], str]:
    try:
        return tap_query_csv(query)
    except Exception:
        return tap_query_votable(query)


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def fetch_table_columns(table_name: str) -> set[str]:
    query = f"""
    SELECT column_name
      FROM TAP_SCHEMA.columns
     WHERE table_name = {sql_quote(table_name)}
    """
    rows, _raw = tap_query(query)
    cols = set()
    for row in rows:
        col = norm(row.get("column_name", ""))
        if col:
            cols.add(col)
    return cols


def choose_columns(available: set[str], wanted: list[str]) -> list[str]:
    return [col for col in wanted if col in available]


def select_targets(conn: sqlite3.Connection, only_new: bool, limit: int):
    if only_new:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.category, t.slug,
               t.ra_deg, t.dec_deg,
               s.target_id AS simbad_target_id
          FROM targets t
          LEFT JOIN target_simbad_resolve s
            ON s.target_id = t.id
         WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND lower(trim(coalesce(t.canonical_name,''))) NOT IN ('sun','moon')
           AND (
                s.target_id IS NULL OR
                coalesce(s.status,'pending') IN ('pending','error','unresolved')
           )
         ORDER BY t.id ASC
         LIMIT ?
        """
    else:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.category, t.slug,
               t.ra_deg, t.dec_deg,
               s.target_id AS simbad_target_id
          FROM targets t
          LEFT JOIN target_simbad_resolve s
            ON s.target_id = t.id
         WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND lower(trim(coalesce(t.canonical_name,''))) NOT IN ('sun','moon')
         ORDER BY t.id ASC
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()

def upsert_simbad(conn: sqlite3.Connection, row: sqlite3.Row, status: str, error_message: str, payload=None):
    canonical_name = norm(row["canonical_name"])
    slug = norm(row["slug"])
    query_name = canonical_name or norm(row["display_name"])
    query_ra_deg = row["ra_deg"]
    query_dec_deg = row["dec_deg"]
    position_source = "base_coords" if query_ra_deg is not None and query_dec_deg is not None else "name_only"

    simbad_main_id = ""
    simbad_otype = ""
    maintype = ""
    simbad_ra_deg = None
    simbad_dec_deg = None
    match_name = ""
    match_ra_deg = None
    match_dec_deg = None
    match_distance_deg = None
    match_method = "name"
    match_confidence = None
    aliases_json = "[]"
    raw_payload = ""
    rv_value = None
    rv_error = None
    rv_quality = ""
    rv_ref = ""
    pmra = None
    pmdec = None
    plx_value = None
    plx_error = None
    bibcode_count = None
    rvz_radvel = None
    rvz_redshift = None
    rvz_type = ""
    rvz_error = None
    rvz_qual = ""
    plx_err = None
    nbref = None
    identifiers_json = "[]"
    photometry_json = "{}"
    tap_basic_json = "{}"

    if payload:
        simbad_main_id = norm(payload.get("simbad_main_id"))
        simbad_otype = norm(payload.get("simbad_otype"))
        maintype = norm(payload.get("maintype"))
        simbad_ra_deg = payload.get("simbad_ra_deg")
        simbad_dec_deg = payload.get("simbad_dec_deg")
        match_name = simbad_main_id or query_name
        match_ra_deg = simbad_ra_deg
        match_dec_deg = simbad_dec_deg
        aliases_json = json.dumps(payload.get("aliases") or [], ensure_ascii=False)
        raw_payload = payload.get("raw_payload") or ""
        rv_value = payload.get("rv_value")
        rv_error = payload.get("rv_error")
        rv_quality = norm(payload.get("rv_quality"))
        rv_ref = norm(payload.get("rv_ref"))
        pmra = payload.get("pmra")
        pmdec = payload.get("pmdec")
        plx_value = payload.get("plx_value")
        plx_error = payload.get("plx_error")
        bibcode_count = payload.get("bibcode_count")
        rvz_radvel = payload.get("rvz_radvel")
        rvz_redshift = payload.get("rvz_redshift")
        rvz_type = norm(payload.get("rvz_type"))
        rvz_error = payload.get("rvz_error")
        rvz_qual = norm(payload.get("rvz_qual"))
        plx_err = payload.get("plx_err")
        nbref = payload.get("nbref")
        identifiers_json = json.dumps(payload.get("identifiers") or [], ensure_ascii=False)
        photometry_json = json.dumps(payload.get("photometry") or {}, ensure_ascii=False)
        tap_basic_json = json.dumps(payload.get("tap_basic") or {}, ensure_ascii=False)

        if query_ra_deg is not None and query_dec_deg is not None and simbad_ra_deg is not None and simbad_dec_deg is not None:
            match_distance_deg = angular_sep_deg(query_ra_deg, query_dec_deg, simbad_ra_deg, simbad_dec_deg)
            match_method = "name+coords"
            if match_distance_deg is not None:
                if match_distance_deg <= 0.01:
                    match_confidence = 0.99
                elif match_distance_deg <= 0.05:
                    match_confidence = 0.95
                elif match_distance_deg <= 0.2:
                    match_confidence = 0.85
                else:
                    match_confidence = 0.60
        else:
            match_confidence = 0.70 if simbad_ra_deg is not None and simbad_dec_deg is not None else 0.50

    conn.execute(
        """
        INSERT INTO target_simbad_resolve (
            target_id, canonical_name, slug, query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            simbad_main_id, simbad_otype, simbad_ra_deg, simbad_dec_deg,
            aliases, raw_payload, rv_value, rv_error, rv_quality, rv_ref,
            pmra, pmdec, plx_value, plx_error, bibcode_count,
            maintype, rvz_radvel, rvz_redshift, rvz_type, rvz_error, rvz_qual,
            plx_err, nbref, identifiers_json, photometry_json, tap_basic_json,
            status, source, error_message, resolved_at, created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, 'simbad', ?, datetime('now'), datetime('now'), datetime('now')
        )
        ON CONFLICT(target_id) DO UPDATE SET
            canonical_name=excluded.canonical_name,
            slug=excluded.slug,
            query_name=excluded.query_name,
            query_ra_deg=excluded.query_ra_deg,
            query_dec_deg=excluded.query_dec_deg,
            position_source=excluded.position_source,
            match_name=excluded.match_name,
            match_ra_deg=excluded.match_ra_deg,
            match_dec_deg=excluded.match_dec_deg,
            match_distance_deg=excluded.match_distance_deg,
            match_method=excluded.match_method,
            match_confidence=excluded.match_confidence,
            simbad_main_id=excluded.simbad_main_id,
            simbad_otype=excluded.simbad_otype,
            simbad_ra_deg=excluded.simbad_ra_deg,
            simbad_dec_deg=excluded.simbad_dec_deg,
            aliases=excluded.aliases,
            raw_payload=excluded.raw_payload,
            rv_value=excluded.rv_value,
            rv_error=excluded.rv_error,
            rv_quality=excluded.rv_quality,
            rv_ref=excluded.rv_ref,
            pmra=excluded.pmra,
            pmdec=excluded.pmdec,
            plx_value=excluded.plx_value,
            plx_error=excluded.plx_error,
            bibcode_count=excluded.bibcode_count,
            maintype=excluded.maintype,
            rvz_radvel=excluded.rvz_radvel,
            rvz_redshift=excluded.rvz_redshift,
            rvz_type=excluded.rvz_type,
            rvz_error=excluded.rvz_error,
            rvz_qual=excluded.rvz_qual,
            plx_err=excluded.plx_err,
            nbref=excluded.nbref,
            identifiers_json=excluded.identifiers_json,
            photometry_json=excluded.photometry_json,
            tap_basic_json=excluded.tap_basic_json,
            status=excluded.status,
            source='simbad',
            error_message=excluded.error_message,
            resolved_at=datetime('now'),
            updated_at=datetime('now')
        """,
        (
            row["id"], canonical_name, slug, query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            simbad_main_id, simbad_otype, simbad_ra_deg, simbad_dec_deg,
            aliases_json, raw_payload, rv_value, rv_error, rv_quality, rv_ref,
            pmra, pmdec, plx_value, plx_error, bibcode_count,
            maintype, rvz_radvel, rvz_redshift, rvz_type, rvz_error, rvz_qual,
            plx_err, nbref, identifiers_json, photometry_json, tap_basic_json,
            status, error_message,
        ),
    )


def update_targets_from_simbad(conn: sqlite3.Connection, row: sqlite3.Row, payload: dict):
    conn.execute(
        """
        UPDATE targets
           SET simbad_main_id=?,
               simbad_otype=?,
               simbad_ra_deg=?,
               simbad_dec_deg=?,
               simbad_status='resolved',
               simbad_source='simbad',
               simbad_resolved_at=datetime('now'),
               updated_at=datetime('now')
         WHERE id=?
        """,
        (
            norm(payload.get("simbad_main_id")),
            norm(payload.get("simbad_otype")),
            payload.get("simbad_ra_deg"),
            payload.get("simbad_dec_deg"),
            row["id"],
        ),
    )


def mark_error(conn: sqlite3.Connection, row: sqlite3.Row, message: str, raw_text: str = ""):
    payload = {"raw_payload": raw_text} if raw_text else None
    upsert_simbad(conn, row, "error", message, payload)
    conn.execute(
        """
        UPDATE targets
           SET simbad_status='error',
               simbad_source='simbad',
               simbad_resolved_at=datetime('now'),
               updated_at=datetime('now')
         WHERE id=?
        """,
        (row["id"],),
    )
    conn.commit()

def score_name_match(query_name: str, candidate_name: str) -> int:
    q_raw = norm(query_name)
    q_norm = normalize_catalog_name(query_name)
    c_raw = norm(candidate_name)
    c_norm = normalize_catalog_name(candidate_name)

    q_raw_c = lower_compact(q_raw)
    q_norm_c = lower_compact(q_norm)
    c_raw_c = lower_compact(c_raw)
    c_norm_c = lower_compact(c_norm)

    if not c_norm_c:
        return 0
    if c_norm_c == q_norm_c:
        return 100
    if c_raw_c == q_raw_c:
        return 90
    if c_norm_c == q_raw_c or c_raw_c == q_norm_c:
        return 80
    if q_norm_c in c_norm_c:
        return 40
    if q_raw_c in c_norm_c:
        return 30
    return 0


def build_basic_query(query_name: str, available_columns: set[str]) -> str:
    selected = choose_columns(available_columns, BASIC_WANTED_COLUMNS)
    required = {"oid", "main_id", "ra", "dec"}
    missing = sorted(required - set(selected))
    if missing:
        raise ValueError(f"SIMBAD TAP basic missing columns: {', '.join(missing)}")

    cols = ", ".join([f"b.{c}" for c in selected])

    q_raw = norm(query_name)
    q_norm = normalize_catalog_name(query_name)

    q1 = sql_quote(q_raw)
    q2 = sql_quote(q_norm)

    return f"""
    SELECT TOP 1 {cols}
      FROM basic b
 LEFT JOIN ident i
        ON i.oidref = b.oid
     WHERE i.id = {q1}
        OR i.id = {q2}
        OR b.main_id = {q1}
        OR b.main_id = {q2}
     ORDER BY
        CASE
            WHEN i.id = {q1} THEN 1
            WHEN i.id = {q2} THEN 2
            WHEN b.main_id = {q1} THEN 3
            WHEN b.main_id = {q2} THEN 4
            ELSE 9
        END
    """


def build_cone_query(ra_deg: float, dec_deg: float, available_columns: set[str], radius_deg: float) -> str:
    selected = choose_columns(available_columns, BASIC_WANTED_COLUMNS)
    required = {"oid", "main_id", "ra", "dec"}
    missing = sorted(required - set(selected))
    if missing:
        raise ValueError(f"SIMBAD TAP basic missing columns: {', '.join(missing)}")

    cols = ", ".join([f"b.{c}" for c in selected])

    return f"""
    SELECT TOP 20 {cols},
           DISTANCE(
               POINT('ICRS', b.ra, b.dec),
               POINT('ICRS', {ra_deg}, {dec_deg})
           ) AS match_sep_deg
      FROM basic b
     WHERE 1 = CONTAINS(
               POINT('ICRS', b.ra, b.dec),
               CIRCLE('ICRS', {ra_deg}, {dec_deg}, {radius_deg})
           )
     ORDER BY match_sep_deg ASC
    """


def build_ident_query(oid_value: str, ident_columns: set[str]) -> str | None:
    if "id" not in ident_columns:
        return None
    oid_str = norm(oid_value)
    if oid_str == "":
        return None
    return f"""
    SELECT id
      FROM ident
     WHERE oidref = {oid_str}
    """


def build_flux_query(oid_value: str, flux_table: str, flux_columns: set[str]) -> str | None:
    if "filter" not in flux_columns:
        return None

    value_col = None
    for candidate in ("flux", "fluxdata", "flux_value", "mag", "magnitude"):
        if candidate in flux_columns:
            value_col = candidate
            break
    if value_col is None:
        return None

    oid_str = norm(oid_value)
    if oid_str == "":
        return None

    pieces = ["filter", f"{value_col} AS value"]
    for candidate in ("flux_err", "flux_error", "flux_qual", "qual", "bibcode"):
        if candidate in flux_columns:
            pieces.append(candidate)

    cols = ", ".join(pieces)
    return f"""
    SELECT {cols}
      FROM {flux_table}
     WHERE oidref = {oid_str}
    """


def fetch_photometry(oid_value: str) -> tuple[dict, dict]:
    raw_map = {}

    for table_name in FLUX_TABLE_CANDIDATES:
        try:
            flux_columns = fetch_table_columns(table_name)
        except Exception:
            continue
        if not flux_columns:
            continue

        query = build_flux_query(oid_value, table_name, flux_columns)
        if not query:
            continue

        try:
            rows, raw = tap_query(query)
        except Exception:
            continue

        raw_map[table_name] = {
            "rows": rows,
            "raw": raw,
        }

        phot = {}
        for row in rows:
            filt = norm(row.get("filter"))
            if not filt:
                continue
            entry = {}
            for k, v in row.items():
                if norm(v) == "":
                    continue
                entry[k] = v
            phot[filt] = entry

        if phot:
            return phot, raw_map

    return {}, raw_map

def resolve_one(conn: sqlite3.Connection, row: sqlite3.Row, basic_columns: set[str], ident_columns: set[str]):
    query_name = norm(row["canonical_name"]) or norm(row["display_name"])
    if not query_name:
        mark_error(conn, row, "empty query name")
        return

    basic_row = None
    basic_raw = ""

    target_ra = row["ra_deg"]
    target_dec = row["dec_deg"]

    if target_ra is not None and target_dec is not None:
        try:
            cone_query = build_cone_query(float(target_ra), float(target_dec), basic_columns, CONE_RADIUS_DEG)
            cone_rows, cone_raw = tap_query(cone_query)
            if cone_rows:
                def sort_key(candidate):
                    sep = parse_float(candidate.get("match_sep_deg"))
                    if sep is None:
                        sep = 999999.0
                    name_score = score_name_match(query_name, candidate.get("main_id", ""))
                    return (sep, -name_score)

                cone_rows.sort(key=sort_key)
                basic_row = cone_rows[0]
                basic_raw = cone_raw
        except Exception:
            basic_row = None
            basic_raw = ""

    if basic_row is None:
        try:
            basic_query = build_basic_query(query_name, basic_columns)
            basic_rows, basic_raw = tap_query(basic_query)
        except Exception as exc:
            mark_error(conn, row, f"tap_basic_error: {exc}")
            return

        if not basic_rows:
            mark_error(conn, row, "tap_basic_no_result", basic_raw[:4000])
            return

        basic_row = basic_rows[0]

    oid_value = norm(basic_row.get("oid"))

    identifiers = []
    ident_raw = ""
    ident_query = build_ident_query(oid_value, ident_columns)
    if ident_query:
        try:
            ident_rows, ident_raw = tap_query(ident_query)
            seen = set()
            for ident_row in ident_rows:
                value = norm(ident_row.get("id"))
                if not value:
                    continue
                key = value.lower()
                if key in seen:
                    continue
                seen.add(key)
                identifiers.append(value)
        except Exception:
            ident_raw = ""

    photometry, phot_raw_map = fetch_photometry(oid_value)

    payload = {
        "simbad_main_id": norm(basic_row.get("main_id")),
        "simbad_otype": norm(basic_row.get("otype")),
        "maintype": norm(basic_row.get("maintype") or basic_row.get("otype_txt")),
        "simbad_ra_deg": parse_float(basic_row.get("ra")),
        "simbad_dec_deg": parse_float(basic_row.get("dec")),
        "pmra": parse_float(basic_row.get("pmra")),
        "pmdec": parse_float(basic_row.get("pmdec")),
        "plx_value": parse_float(basic_row.get("plx_value")),
        "plx_error": parse_float(basic_row.get("plx_err")),
        "rvz_radvel": parse_float(basic_row.get("rvz_radvel")),
        "rvz_redshift": parse_float(basic_row.get("rvz_redshift")),
        "rvz_type": norm(basic_row.get("rvz_type")),
        "rvz_error": parse_float(basic_row.get("rvz_error")),
        "rvz_qual": norm(basic_row.get("rvz_qual")),
        "nbref": parse_int(basic_row.get("nbref")),
        "aliases": identifiers[:],
        "identifiers": identifiers,
        "photometry": photometry,
        "tap_basic": basic_row,
        "raw_payload": json.dumps(
            {
                "basic_raw": basic_raw,
                "ident_raw": ident_raw,
                "phot_raw": phot_raw_map,
            },
            ensure_ascii=False,
        ),
    }

    upsert_simbad(conn, row, "resolved", "", payload)
    update_targets_from_simbad(conn, row, payload)
    conn.commit()


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        basic_columns = fetch_table_columns("basic")
        ident_columns = fetch_table_columns("ident")
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_simbad_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            try:
                resolve_one(conn, row, basic_columns, ident_columns)
            except Exception as exc:
                mark_error(conn, row, f"resolve_error: {exc}")
            time.sleep(0.25)
    finally:
        conn.close()
    return 0
