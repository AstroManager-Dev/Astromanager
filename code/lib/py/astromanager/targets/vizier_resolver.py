#!/usr/bin/env python3
import csv
import io
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "25"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
VIZIER_TAP_SYNC_URL = os.environ.get(
    "TARGET_RESOLVER_VIZIER_TAP_SYNC_URL",
    "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
)
VIZIER_TABLE = os.environ.get("TARGET_RESOLVER_VIZIER_TABLE", '"VII/118/ngc2000"')
VIZIER_RADIUS_DEG = float(os.environ.get("TARGET_RESOLVER_VIZIER_RADIUS_DEG", "0.2"))


def db():
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


def tap_query_csv(query: str):
    raw = http_post_text(
        VIZIER_TAP_SYNC_URL,
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


def tap_query_votable(query: str):
    raw = http_post_text(
        VIZIER_TAP_SYNC_URL,
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


def tap_query(query: str):
    try:
        return tap_query_csv(query)
    except Exception:
        return tap_query_votable(query)


def is_system_target(row) -> bool:
    canonical = norm(row["canonical_name"]).lower()
    category = norm(row["category"]).lower()
    return canonical in {"sun", "moon"} or category in {"sun", "moon"}


def select_targets(conn, only_new: bool, limit: int):
    if only_new:
        sql = """
        SELECT
            t.id,
            t.canonical_name,
            t.display_name,
            t.final_name,
            t.category,
            t.final_ra_deg,
            t.final_dec_deg,
            v.target_id AS vizier_target_id,
            v.status AS vizier_status
        FROM targets t
        LEFT JOIN target_vizier_resolve v
          ON v.target_id = t.id
        WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
          AND (
                v.target_id IS NULL
                OR coalesce(v.status,'pending') IN ('pending','error','unresolved')
              )
        ORDER BY t.id
        LIMIT ?
        """
    else:
        sql = """
        SELECT
            t.id,
            t.canonical_name,
            t.display_name,
            t.final_name,
            t.category,
            t.final_ra_deg,
            t.final_dec_deg,
            v.target_id AS vizier_target_id,
            v.status AS vizier_status
        FROM targets t
        LEFT JOIN target_vizier_resolve v
          ON v.target_id = t.id
        WHERE lower(coalesce(t.category,'')) NOT IN ('sun','moon')
        ORDER BY t.id
        LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def upsert_vizier(conn, row, status: str, error_message: str, payload=None):
    query_name = norm(row["final_name"]) or norm(row["display_name"]) or norm(row["canonical_name"])
    query_ra_deg = row["final_ra_deg"]
    query_dec_deg = row["final_dec_deg"]
    position_source = "targets.final_coords" if query_ra_deg is not None and query_dec_deg is not None else "name_only"

    match_name = ""
    match_ra_deg = None
    match_dec_deg = None
    match_distance_deg = None
    match_method = "position"
    match_confidence = None

    preferred_name = ""
    aliases = "[]"
    object_type = ""
    object_type_label = ""
    ra_deg = None
    dec_deg = None
    ra_text = ""
    dec_text = ""
    magnitude_value = None
    magnitude_band = ""
    identifier_count = None
    raw_payload = ""
    catalog_source = ""
    main_id = ""
    resource_name = ""
    resource_title = ""
    resource_ivoid = ""
    data_ivoid = ""
    creator = ""
    bibcode = ""
    journal = ""
    original_date = ""
    reference_url = ""
    publication_date = ""
    rights_uri = ""
    table_name = ""
    catalog_code = ""
    ngc_ic = ""
    ngc_ic_component = ""
    ra_b1950 = ""
    dec_b1950 = ""
    pos_quality = ""
    pos_flag = ""
    pos_ref = ""
    obs_count = None
    comment_text = ""
    simbad_ref = ""
    ned_ref = ""

    if payload:
        preferred_name = norm(payload.get("preferred_name"))
        aliases = payload.get("aliases_json") or "[]"
        object_type = norm(payload.get("object_type"))
        object_type_label = norm(payload.get("object_type_label"))
        ra_deg = payload.get("ra_deg")
        dec_deg = payload.get("dec_deg")
        ra_text = norm(payload.get("ra_text"))
        dec_text = norm(payload.get("dec_text"))
        magnitude_value = payload.get("magnitude_value")
        magnitude_band = norm(payload.get("magnitude_band"))
        identifier_count = payload.get("identifier_count")
        raw_payload = payload.get("raw_payload") or ""
        catalog_source = norm(payload.get("catalog_source"))
        main_id = norm(payload.get("main_id"))
        resource_name = norm(payload.get("resource_name"))
        resource_title = norm(payload.get("resource_title"))
        resource_ivoid = norm(payload.get("resource_ivoid"))
        data_ivoid = norm(payload.get("data_ivoid"))
        creator = norm(payload.get("creator"))
        bibcode = norm(payload.get("bibcode"))
        journal = norm(payload.get("journal"))
        original_date = norm(payload.get("original_date"))
        reference_url = norm(payload.get("reference_url"))
        publication_date = norm(payload.get("publication_date"))
        rights_uri = norm(payload.get("rights_uri"))
        table_name = norm(payload.get("table_name"))
        catalog_code = norm(payload.get("catalog_code"))
        ngc_ic = norm(payload.get("ngc_ic"))
        ngc_ic_component = norm(payload.get("ngc_ic_component"))
        ra_b1950 = norm(payload.get("ra_b1950"))
        dec_b1950 = norm(payload.get("dec_b1950"))
        pos_quality = norm(payload.get("pos_quality"))
        pos_flag = norm(payload.get("pos_flag"))
        pos_ref = norm(payload.get("pos_ref"))
        obs_count = payload.get("obs_count")
        comment_text = norm(payload.get("comment_text"))
        simbad_ref = norm(payload.get("simbad_ref"))
        ned_ref = norm(payload.get("ned_ref"))

        match_name = preferred_name or query_name
        match_ra_deg = ra_deg
        match_dec_deg = dec_deg

        if query_ra_deg is not None and query_dec_deg is not None and ra_deg is not None and dec_deg is not None:
            match_distance_deg = angular_sep_deg(query_ra_deg, query_dec_deg, ra_deg, dec_deg)
            if match_distance_deg is not None:
                if match_distance_deg <= 0.001:
                    match_confidence = 0.99
                elif match_distance_deg <= 0.01:
                    match_confidence = 0.95
                elif match_distance_deg <= 0.05:
                    match_confidence = 0.85
                else:
                    match_confidence = 0.60
        else:
            match_confidence = 0.50

    conn.execute(
        """
        INSERT INTO target_vizier_resolve (
            target_id, canonical_name, slug,
            query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            catalog_source, main_id, preferred_name, aliases, object_type, object_type_label,
            ra_deg, dec_deg, ra_text, dec_text,
            magnitude_value, magnitude_band, identifier_count,
            status, source, error_message, request_url, raw_payload, resolved_at, created_at, updated_at,
            resource_name, resource_title, resource_ivoid, data_ivoid, creator, bibcode, journal,
            original_date, reference_url, publication_date, rights_uri, table_name, catalog_code,
            ngc_ic, ngc_ic_component, ra_b1950, dec_b1950, pos_quality, pos_flag, pos_ref,
            obs_count, comment_text, simbad_ref, ned_ref
        )
        VALUES (
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, 'vizier_tap', ?, ?, ?, datetime('now'), datetime('now'), datetime('now'),
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?
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
            catalog_source=excluded.catalog_source,
            main_id=excluded.main_id,
            preferred_name=excluded.preferred_name,
            aliases=excluded.aliases,
            object_type=excluded.object_type,
            object_type_label=excluded.object_type_label,
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            ra_text=excluded.ra_text,
            dec_text=excluded.dec_text,
            magnitude_value=excluded.magnitude_value,
            magnitude_band=excluded.magnitude_band,
            identifier_count=excluded.identifier_count,
            status=excluded.status,
            source='vizier_tap',
            error_message=excluded.error_message,
            request_url=excluded.request_url,
            raw_payload=excluded.raw_payload,
            resolved_at=datetime('now'),
            resource_name=excluded.resource_name,
            resource_title=excluded.resource_title,
            resource_ivoid=excluded.resource_ivoid,
            data_ivoid=excluded.data_ivoid,
            creator=excluded.creator,
            bibcode=excluded.bibcode,
            journal=excluded.journal,
            original_date=excluded.original_date,
            reference_url=excluded.reference_url,
            publication_date=excluded.publication_date,
            rights_uri=excluded.rights_uri,
            table_name=excluded.table_name,
            catalog_code=excluded.catalog_code,
            ngc_ic=excluded.ngc_ic,
            ngc_ic_component=excluded.ngc_ic_component,
            ra_b1950=excluded.ra_b1950,
            dec_b1950=excluded.dec_b1950,
            pos_quality=excluded.pos_quality,
            pos_flag=excluded.pos_flag,
            pos_ref=excluded.pos_ref,
            obs_count=excluded.obs_count,
            comment_text=excluded.comment_text,
            simbad_ref=excluded.simbad_ref,
            ned_ref=excluded.ned_ref,
            updated_at=datetime('now')
        """,
        (
            row["id"], norm(row["canonical_name"]), "",
            query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            catalog_source, main_id, preferred_name, aliases, object_type, object_type_label,
            ra_deg, dec_deg, ra_text, dec_text,
            magnitude_value, magnitude_band, identifier_count,
            status, error_message, VIZIER_TAP_SYNC_URL, raw_payload,
            resource_name, resource_title, resource_ivoid, data_ivoid, creator, bibcode, journal,
            original_date, reference_url, publication_date, rights_uri, table_name, catalog_code,
            ngc_ic, ngc_ic_component, ra_b1950, dec_b1950, pos_quality, pos_flag, pos_ref,
            obs_count, comment_text, simbad_ref, ned_ref,
        ),
    )


def build_query(ra_deg: float, dec_deg: float, radius_deg: float) -> str:
    return f"""
    SELECT TOP 25
        "Name",
        "Type",
        "Desc",
        "RAB2000",
        "DEB2000",
        "mag",
        "n_mag",
        "Const",
        "Source",
        "size",
        "l_size"
    FROM {VIZIER_TABLE}
    WHERE 1=CONTAINS(
        POINT('ICRS', "RAB2000", "DEB2000"),
        CIRCLE('ICRS', {float(ra_deg)}, {float(dec_deg)}, {float(radius_deg)})
    )
    """.strip()


def resolve_one(conn, row):
    if is_system_target(row):
        upsert_vizier(conn, row, "skipped", "", None)
        conn.commit()
        return

    ra_deg = row["final_ra_deg"]
    dec_deg = row["final_dec_deg"]

    if ra_deg is None or dec_deg is None:
        upsert_vizier(conn, row, "pending", "missing final coordinates", None)
        conn.commit()
        return

    try:
        query = build_query(float(ra_deg), float(dec_deg), VIZIER_RADIUS_DEG)
        rows, raw = tap_query(query)
    except Exception as exc:
        upsert_vizier(conn, row, "error", f"tap_error: {exc}", {"raw_payload": ""})
        conn.commit()
        return

    if not rows:
        upsert_vizier(conn, row, "unresolved", "no_match", {"raw_payload": raw[:12000]})
        conn.commit()
        return

    best = None
    best_sep = None

    for candidate in rows:
        cand_ra = parse_float(candidate.get("RAB2000"))
        cand_dec = parse_float(candidate.get("DEB2000"))
        sep = angular_sep_deg(ra_deg, dec_deg, cand_ra, cand_dec)
        if best is None or (sep is not None and (best_sep is None or sep < best_sep)):
            best = candidate
            best_sep = sep

    main_id = norm(best.get("Name"))
    mag_band = "photographic" if norm(best.get("n_mag")).lower() == "p" else "visual"
    desc = norm(best.get("Desc"))
    size = norm(best.get("size"))
    l_size = norm(best.get("l_size"))
    comment_parts = [x for x in [desc, f"size={l_size}{size}" if size else ""] if x]

    payload = {
        "catalog_source": "VizieR TAP",
        "main_id": main_id,
        "preferred_name": main_id,
        "aliases_json": "[]",
        "object_type": norm(best.get("Type")),
        "object_type_label": norm(best.get("Type")),
        "ra_deg": parse_float(best.get("RAB2000")),
        "dec_deg": parse_float(best.get("DEB2000")),
        "ra_text": norm(best.get("RAB2000")),
        "dec_text": norm(best.get("DEB2000")),
        "magnitude_value": parse_float(best.get("mag")),
        "magnitude_band": mag_band if parse_float(best.get("mag")) is not None else "",
        "identifier_count": 1 if main_id else 0,
        "raw_payload": raw[:12000],
        "resource_name": "VII/118/ngc2000",
        "resource_title": "NGC 2000.0 Catalogue",
        "table_name": "VII/118/ngc2000",
        "catalog_code": "VII/118",
        "ngc_ic": main_id,
        "ngc_ic_component": "",
        "ra_b1950": norm(best.get("RAB2000")),
        "dec_b1950": norm(best.get("DEB2000")),
        "pos_quality": "",
        "pos_flag": "",
        "pos_ref": norm(best.get("Source")),
        "obs_count": None,
        "comment_text": " | ".join(comment_parts),
        "simbad_ref": "",
        "ned_ref": "",
    }

    upsert_vizier(conn, row, "resolved", "", payload)
    conn.commit()


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_vizier_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.15)
    finally:
        conn.close()

    return 0
