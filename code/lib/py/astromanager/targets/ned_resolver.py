#!/usr/bin/env python3
import json
import math
import os
import sqlite3
import time
import urllib.request

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "20"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
NED_URL = os.environ.get("TARGET_RESOLVER_NED_URL", "https://ned.ipac.caltech.edu/srs/ObjectLookup")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(v):
    return " ".join(str(v or "").strip().split())


def parse_float(v):
    try:
        return float(v)
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
        math.sin(dec1r) * math.sin(dec2r) +
        math.cos(dec1r) * math.cos(dec2r) * math.cos(ra1r - ra2r)
    )
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


def confidence_from_sep(sep):
    if sep is None:
        return 0.70
    if sep <= 0.01:
        return 0.99
    if sep <= 0.05:
        return 0.95
    if sep <= 0.2:
        return 0.85
    return 0.55


def http_post_json(url: str, payload: dict):
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def is_system_target(row):
    canonical = norm(row["canonical_name"]).lower()
    category = norm(row["category"]).lower()
    return canonical in {"sun", "moon"} or category in {"sun", "moon"}


def select_targets(conn, only_new: bool, limit: int):
    if only_new:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.category, t.slug,
               t.ra_deg, t.dec_deg,
               n.target_id AS ned_target_id,
               n.status AS ned_status
          FROM targets t
          LEFT JOIN target_ned_resolve n
            ON n.target_id = t.id
         WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND lower(trim(coalesce(t.canonical_name,''))) NOT IN ('sun','moon')
           AND (
                n.target_id IS NULL OR
                coalesce(n.status,'pending') IN ('pending','error','unresolved')
           )
         ORDER BY t.id ASC
         LIMIT ?
        """
    else:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.category, t.slug,
               t.ra_deg, t.dec_deg,
               n.target_id AS ned_target_id,
               n.status AS ned_status
          FROM targets t
          LEFT JOIN target_ned_resolve n
            ON n.target_id = t.id
         WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND lower(trim(coalesce(t.canonical_name,''))) NOT IN ('sun','moon')
         ORDER BY t.id ASC
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def parse_ned_payload(data: dict):
    preferred = data.get("Preferred") or {}
    position = preferred.get("Position") or {}
    objtype = preferred.get("ObjType") or {}
    redshift = preferred.get("Redshift") or {}
    interpreted = data.get("Interpreted") or {}

    return {
        "preferred_name": norm(preferred.get("Name")),
        "interpreted_name": norm(interpreted.get("Name")),
        "objtype": norm(objtype.get("Value")),
        "objtype_refcode": norm(objtype.get("RefCode")),
        "ra_deg": parse_float(position.get("RA")),
        "dec_deg": parse_float(position.get("Dec")),
        "position_refcode": norm(position.get("RefCode")),
        "redshift": parse_float(redshift.get("Value")),
        "redshift_uncertainty": parse_float(redshift.get("Uncertainty")),
        "redshift_refcode": norm(redshift.get("RefCode")),
        "redshift_quality": norm(redshift.get("QualityFlag")),
        "status_code": data.get("StatusCode"),
        "result_code": data.get("ResultCode"),
        "resolver_name": norm(data.get("NameResolver")),
        "raw_payload": json.dumps(data, ensure_ascii=False),
    }


def upsert_ned(conn, row, status: str, error_message: str, payload):
    query_name = norm(row["canonical_name"]) or norm(row["display_name"])
    query_ra_deg = row["ra_deg"]
    query_dec_deg = row["dec_deg"]
    position_source = "base_coords" if query_ra_deg is not None and query_dec_deg is not None else "name_only"

    match_name = ""
    match_ra_deg = None
    match_dec_deg = None
    match_distance_deg = None
    match_method = "name"
    match_confidence = None
    ned_preferred_name = ""
    ned_interpreted_name = ""
    ned_objtype = ""
    ned_position_refcode = ""
    ned_objtype_refcode = ""
    ned_redshift = None
    ned_redshift_uncertainty = None
    ned_redshift_refcode = ""
    ned_redshift_quality = ""
    ned_status_code = None
    ned_result_code = None
    ned_resolver_name = ""
    raw_payload = ""

    if payload:
        ned_preferred_name = norm(payload.get("preferred_name"))
        ned_interpreted_name = norm(payload.get("interpreted_name"))
        ned_objtype = norm(payload.get("objtype"))
        ned_position_refcode = norm(payload.get("position_refcode"))
        ned_objtype_refcode = norm(payload.get("objtype_refcode"))
        ned_redshift = payload.get("redshift")
        ned_redshift_uncertainty = payload.get("redshift_uncertainty")
        ned_redshift_refcode = norm(payload.get("redshift_refcode"))
        ned_redshift_quality = norm(payload.get("redshift_quality"))
        ned_status_code = payload.get("status_code")
        ned_result_code = payload.get("result_code")
        ned_resolver_name = norm(payload.get("resolver_name"))
        raw_payload = payload.get("raw_payload") or ""

        match_name = ned_preferred_name or ned_interpreted_name or query_name
        match_ra_deg = payload.get("ra_deg")
        match_dec_deg = payload.get("dec_deg")

        if query_ra_deg is not None and query_dec_deg is not None and match_ra_deg is not None and match_dec_deg is not None:
            match_distance_deg = angular_sep_deg(query_ra_deg, query_dec_deg, match_ra_deg, match_dec_deg)
            match_method = "name+coords"

        match_confidence = confidence_from_sep(match_distance_deg)

    conn.execute(
        """
        INSERT INTO target_ned_resolve (
            target_id, canonical_name, slug,
            query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            ned_preferred_name, ned_interpreted_name,
            ned_objtype, ned_position_refcode, ned_objtype_refcode,
            ned_ra_deg, ned_dec_deg,
            ned_redshift, ned_redshift_uncertainty, ned_redshift_refcode, ned_redshift_quality,
            ned_status_code, ned_result_code, ned_resolver_name,
            raw_payload,
            status, source, error_message, resolved_at, created_at, updated_at
        )
        VALUES (
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?,
            ?, 'ned', ?, datetime('now'), datetime('now'), datetime('now')
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
            ned_preferred_name=excluded.ned_preferred_name,
            ned_interpreted_name=excluded.ned_interpreted_name,
            ned_objtype=excluded.ned_objtype,
            ned_position_refcode=excluded.ned_position_refcode,
            ned_objtype_refcode=excluded.ned_objtype_refcode,
            ned_ra_deg=excluded.ned_ra_deg,
            ned_dec_deg=excluded.ned_dec_deg,
            ned_redshift=excluded.ned_redshift,
            ned_redshift_uncertainty=excluded.ned_redshift_uncertainty,
            ned_redshift_refcode=excluded.ned_redshift_refcode,
            ned_redshift_quality=excluded.ned_redshift_quality,
            ned_status_code=excluded.ned_status_code,
            ned_result_code=excluded.ned_result_code,
            ned_resolver_name=excluded.ned_resolver_name,
            raw_payload=excluded.raw_payload,
            status=excluded.status,
            source='ned',
            error_message=excluded.error_message,
            resolved_at=datetime('now'),
            updated_at=datetime('now')
        """,
        (
            row["id"], norm(row["canonical_name"]), norm(row["slug"]),
            query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            ned_preferred_name, ned_interpreted_name,
            ned_objtype, ned_position_refcode, ned_objtype_refcode,
            match_ra_deg, match_dec_deg,
            ned_redshift, ned_redshift_uncertainty, ned_redshift_refcode, ned_redshift_quality,
            ned_status_code, ned_result_code, ned_resolver_name,
            raw_payload,
            status, error_message,
        ),
    )


def update_targets_from_ned(conn, row, payload):
    conn.execute(
        """
        UPDATE targets
           SET ned_preferred_name=?,
               ned_objtype=?,
               ned_ra_deg=COALESCE(?, ned_ra_deg),
               ned_dec_deg=COALESCE(?, ned_dec_deg),
               ned_status='resolved',
               ned_source='ned',
               ned_resolved_at=datetime('now'),
               updated_at=datetime('now')
         WHERE id=?
        """,
        (
            norm(payload.get("preferred_name")),
            norm(payload.get("objtype")),
            payload.get("ra_deg"),
            payload.get("dec_deg"),
            row["id"],
        ),
    )


def resolve_one(conn, row):
    if is_system_target(row):
        return

    query_name = norm(row["canonical_name"]) or norm(row["display_name"])
    if not query_name:
        upsert_ned(conn, row, "error", "empty query name", None)
        conn.commit()
        return

    try:
        data = http_post_json(NED_URL, {"name": {"v": query_name}})
    except Exception as exc:
        upsert_ned(conn, row, "error", f"http_error: {exc}", None)
        conn.commit()
        return

    payload = parse_ned_payload(data)

    if not payload.get("preferred_name") and payload.get("ra_deg") is None and payload.get("dec_deg") is None:
        upsert_ned(conn, row, "unresolved", "no_match", payload)
        conn.commit()
        return

    upsert_ned(conn, row, "resolved", "", payload)
    update_targets_from_ned(conn, row, payload)
    conn.commit()


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_ned_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.25)
    finally:
        conn.close()

    return 0
