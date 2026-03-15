#!/usr/bin/env python3
import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "20"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
SESAME_BASE = os.environ.get(
    "TARGET_RESOLVER_SESAME_BASE",
    "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/"
)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(value) -> str:
    return " ".join(str(value or "").strip().split())


def parse_float(value):
    try:
        return float(value)
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


def build_url(name: str) -> str:
    name = norm(name)
    if not name:
        raise ValueError("empty query name")
    return SESAME_BASE + "?" + urllib.parse.quote_plus(name)


def http_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/xml,text/xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_xml_document(raw_text: str) -> str:
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    start = raw_text.find("<?xml")
    if start == -1:
        start = raw_text.find("<Sesame")
    if start == -1:
        raise ValueError("no xml start tag found")
    end = raw_text.rfind("</Sesame>")
    if end == -1:
        raise ValueError("no closing </Sesame> tag found")
    end += len("</Sesame>")
    xml_text = raw_text[start:end].strip()
    if not xml_text:
        raise ValueError("empty xml fragment")
    return xml_text


def xml_text(root: ET.Element, path: str) -> str:
    node = root.find(path)
    if node is None or node.text is None:
        return ""
    return norm(node.text)


def parse_sesame_xml(raw_text: str) -> dict:
    xml_doc = extract_xml_document(raw_text)
    root = ET.fromstring(xml_doc)

    target = root.find(".//Target")
    chosen = target if target is not None else root

    resolver = chosen.find(".//Resolver")
    chosen2 = resolver if resolver is not None else chosen

    aliases = []
    for path in (".//oname", ".//alias", ".//id", ".//obj", ".//name"):
        for node in chosen2.findall(path):
            if node.text:
                value = norm(node.text)
                if value and value not in aliases:
                    aliases.append(value)

    data = {
        "resolver_name": "sesame",
        "sesame_oid": xml_text(chosen2, ".//oid"),
        "sesame_oname": xml_text(chosen2, ".//oname"),
        "sesame_otype": xml_text(chosen2, ".//otype"),
        "sesame_mtype": xml_text(chosen2, ".//otype_txt"),
        "ra_deg": parse_float(xml_text(chosen2, ".//jradeg")),
        "dec_deg": parse_float(xml_text(chosen2, ".//jdedeg")),
        "coord_text": xml_text(chosen2, ".//jpos"),
        "coord_ref": xml_text(chosen2, ".//refPos"),
        "vel_value": parse_float(xml_text(chosen2, ".//Vel/v")),
        "vel_error": parse_float(xml_text(chosen2, ".//Vel/e")),
        "vel_quality": xml_text(chosen2, ".//Vel/q"),
        "vel_ref": xml_text(chosen2, ".//Vel/r"),
        "nrefs": None,
        "aliases": aliases,
        "raw_payload": raw_text,
    }

    nrefs_text = xml_text(chosen2, ".//nrefs")
    try:
        data["nrefs"] = int(nrefs_text) if nrefs_text else None
    except Exception:
        data["nrefs"] = None

    return data


def is_system_target(row: sqlite3.Row) -> bool:
    canonical = norm(row["canonical_name"]).lower()
    category = norm(row["category"]).lower()
    return canonical in {"sun", "moon"} or category in {"sun", "moon"}


def select_targets(conn: sqlite3.Connection, only_new: bool, limit: int):
    if only_new:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.category, t.slug,
               t.ra_deg, t.dec_deg,
               s.target_id AS sesame_target_id
          FROM targets t
          LEFT JOIN target_sesame_resolve s
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
               s.target_id AS sesame_target_id
          FROM targets t
          LEFT JOIN target_sesame_resolve s
            ON s.target_id = t.id
         WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND lower(trim(coalesce(t.canonical_name,''))) NOT IN ('sun','moon')
         ORDER BY t.id ASC
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def upsert_sesame(conn: sqlite3.Connection, row: sqlite3.Row, status: str, error_message: str, payload: dict | None):
    raw_payload = json.dumps(payload, ensure_ascii=False) if payload is not None else ""

    canonical_name = norm(row["canonical_name"])
    slug = norm(row["slug"])
    query_name = canonical_name or norm(row["display_name"])
    query_ra_deg = row["ra_deg"]
    query_dec_deg = row["dec_deg"]
    position_source = "base_coords" if query_ra_deg is not None and query_dec_deg is not None else "name_only"

    sesame_oid = ""
    sesame_oname = ""
    sesame_otype = ""
    sesame_mtype = ""
    match_ra_deg = None
    match_dec_deg = None
    coord_text = ""
    coord_ref = ""
    vel_value = None
    vel_error = None
    vel_quality = ""
    vel_ref = ""
    nrefs = None
    aliases_json = "[]"
    match_name = ""
    match_distance_deg = None
    match_method = "name"
    match_confidence = None

    if payload:
        sesame_oid = norm(payload.get("sesame_oid"))
        sesame_oname = norm(payload.get("sesame_oname"))
        sesame_otype = norm(payload.get("sesame_otype"))
        sesame_mtype = norm(payload.get("sesame_mtype"))
        match_ra_deg = payload.get("ra_deg")
        match_dec_deg = payload.get("dec_deg")
        coord_text = norm(payload.get("coord_text"))
        coord_ref = norm(payload.get("coord_ref"))
        vel_value = payload.get("vel_value")
        vel_error = payload.get("vel_error")
        vel_quality = norm(payload.get("vel_quality"))
        vel_ref = norm(payload.get("vel_ref"))
        nrefs = payload.get("nrefs")
        aliases_json = json.dumps(payload.get("aliases") or [], ensure_ascii=False)
        match_name = sesame_oname or query_name
        if query_ra_deg is not None and query_dec_deg is not None and match_ra_deg is not None and match_dec_deg is not None:
            match_distance_deg = angular_sep_deg(query_ra_deg, query_dec_deg, match_ra_deg, match_dec_deg)
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
            match_confidence = 0.70 if match_ra_deg is not None and match_dec_deg is not None else 0.50

    conn.execute(
        """
        INSERT INTO target_sesame_resolve (
            target_id, canonical_name, slug, query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            resolver_name, sesame_oid, sesame_oname, sesame_otype, sesame_mtype,
            ra_deg, dec_deg, coord_text, coord_ref,
            vel_value, vel_error, vel_quality, vel_ref, nrefs, aliases,
            status, source, error_message, raw_payload, resolved_at,
            created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            'sesame', ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, 'sesame', ?, ?, datetime('now'),
            datetime('now'), datetime('now')
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
            resolver_name='sesame',
            sesame_oid=excluded.sesame_oid,
            sesame_oname=excluded.sesame_oname,
            sesame_otype=excluded.sesame_otype,
            sesame_mtype=excluded.sesame_mtype,
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            coord_text=excluded.coord_text,
            coord_ref=excluded.coord_ref,
            vel_value=excluded.vel_value,
            vel_error=excluded.vel_error,
            vel_quality=excluded.vel_quality,
            vel_ref=excluded.vel_ref,
            nrefs=excluded.nrefs,
            aliases=excluded.aliases,
            status=excluded.status,
            source='sesame',
            error_message=excluded.error_message,
            raw_payload=excluded.raw_payload,
            resolved_at=datetime('now'),
            updated_at=datetime('now')
        """,
        (
            row["id"], canonical_name, slug, query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            sesame_oid, sesame_oname, sesame_otype, sesame_mtype,
            match_ra_deg, match_dec_deg, coord_text, coord_ref,
            vel_value, vel_error, vel_quality, vel_ref, nrefs, aliases_json,
            status, error_message, raw_payload,
        ),
    )


def update_targets_from_sesame(conn: sqlite3.Connection, row: sqlite3.Row, payload: dict):
    conn.execute(
        """
        UPDATE targets
           SET ra_deg=?,
               dec_deg=?,
               coord_text=?,
               coord_ref=?,
               coord_status='resolved',
               coord_source='sesame',
               updated_at=datetime('now')
         WHERE id=?
        """,
        (
            payload.get("ra_deg"),
            payload.get("dec_deg"),
            norm(payload.get("coord_text")),
            norm(payload.get("coord_ref")),
            row["id"],
        ),
    )


def mark_error(conn: sqlite3.Connection, row: sqlite3.Row, message: str, raw_payload=None):
    payload = {"raw_payload": raw_payload} if raw_payload is not None else None
    upsert_sesame(conn, row, "error", message, payload)
    conn.commit()


def resolve_one(conn: sqlite3.Connection, row: sqlite3.Row):
    if is_system_target(row):
        return

    query_name = norm(row["canonical_name"]) or norm(row["display_name"])
    if not query_name:
        mark_error(conn, row, "empty query name")
        return

    url = build_url(query_name)

    try:
        raw_text = http_get_text(url)
    except Exception as exc:
        mark_error(conn, row, f"http_error: {exc}")
        return

    try:
        payload = parse_sesame_xml(raw_text)
        payload["query_name"] = query_name
        payload["request_url"] = url
    except Exception as exc:
        mark_error(conn, row, f"xml_parse_error: {exc}", raw_text[:2000])
        return

    upsert_sesame(conn, row, "resolved", "", payload)
    update_targets_from_sesame(conn, row, payload)
    conn.commit()


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_sesame_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.25)
    finally:
        conn.close()

    return 0
