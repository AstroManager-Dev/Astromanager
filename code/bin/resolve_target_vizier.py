#!/usr/bin/env python3
import math
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "20"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
VIZIER_BASE = os.environ.get("TARGET_RESOLVER_VIZIER_BASE", "https://vizier.cds.unistra.fr/viz-bin/asu-tsv")
VIZIER_SOURCE = os.environ.get("TARGET_RESOLVER_VIZIER_SOURCE", "VII/239")
VIZIER_RADIUS = os.environ.get("TARGET_RESOLVER_VIZIER_RADIUS", "0.2")

PLACEHOLDER_VALUES = {
    "", "-", "--", "---", "----", "-----", "------", "-------", "--------",
    "---------", "----------", "-------------",
}

# Gezielt nur die für das Matching und spätere UI relevanten Felder anfordern.
# _RA.icrs / _DE.icrs sind in VizieR oft die robusteren ICRS-Positionsfelder.
VIZIER_OUT_COLUMNS = [
    "NGC/IC",
    "n_NGC/IC",
    "RAB1950",
    "DEB1950",
    "qPos",
    "f_Pos",
    "r_Pos",
    "N",
    "Comm",
    "Simbad",
    "NED",
    "_RA.icrs",
    "_DE.icrs",
]

# Nach Distanz sortieren, wenn VizieR das für die Abfrage unterstützt.
VIZIER_SORT_COLUMNS = ["_r"]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(v):
    return " ".join(str(v or "").strip().split())


def clean_value(v: str) -> str:
    text = norm(v)
    if text in PLACEHOLDER_VALUES:
        return ""
    if text and set(text) <= {"-"}:
        return ""
    return text


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


def http_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,text/tab-separated-values,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build_url(query_name: str, ra_deg: float, dec_deg: float) -> str:
    params = [
        ("-source", VIZIER_SOURCE),
        ("-c", f"{ra_deg} {dec_deg}"),
        ("-c.rs", str(VIZIER_RADIUS)),
        ("-out.meta", "hu"),
    ]

    for col in VIZIER_OUT_COLUMNS:
        params.append(("-out", col))

    for col in VIZIER_SORT_COLUMNS:
        params.append(("-sort", col))

    return VIZIER_BASE + "?" + urllib.parse.urlencode(params)


def select_targets(conn, only_new: bool, limit: int):
    if only_new:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.final_name, t.slug,
               t.final_ra_deg, t.final_dec_deg,
               v.target_id AS vizier_target_id,
               v.status AS vizier_status
          FROM targets t
          LEFT JOIN target_vizier_resolve v
            ON v.target_id = t.id
         WHERE t.final_ra_deg IS NOT NULL
           AND t.final_dec_deg IS NOT NULL
           AND lower(coalesce(t.category,'')) NOT IN ('sun','moon')
           AND (
                v.target_id IS NULL OR
                coalesce(v.status,'pending') IN ('pending','error','unresolved')
           )
         ORDER BY t.id ASC
         LIMIT ?
        """
    else:
        sql = """
        SELECT t.id, t.canonical_name, t.display_name, t.final_name, t.slug,
               t.final_ra_deg, t.final_dec_deg,
               v.target_id AS vizier_target_id,
               v.status AS vizier_status
          FROM targets t
          LEFT JOIN target_vizier_resolve v
            ON v.target_id = t.id
         WHERE t.final_ra_deg IS NOT NULL
           AND t.final_dec_deg IS NOT NULL
           AND lower(coalesce(t.category,'')) NOT IN ('sun','moon')
         ORDER BY t.id ASC
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def parse_header_value(line: str):
    line = line.rstrip("\n")
    if not line.startswith("#INFO"):
        return None
    payload = norm(line[5:])
    if "=" not in payload:
        return None
    key, value = payload.split("=", 1)
    return norm(key), norm(value.split("\t")[0])


def parse_resource_value(line: str):
    line = line.rstrip("\n")
    if not line.startswith("#"):
        return None
    if line.startswith("#INFO") or line.startswith("##") or line.startswith("#Column"):
        return None
    body = line[1:]
    if ":" in body:
        key, value = body.split(":", 1)
        return norm(key), norm(value)
    if "=" in body:
        key, value = body.split("=", 1)
        return norm(key), norm(value)
    return None


def is_separator_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("----") or stripped.startswith("===="):
        return True
    if set(stripped) <= {"-", "=", " "}:
        return True
    return False


def first_row_value(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row:
            return clean_value(row.get(key))
    return ""


def is_real_data_row(row: dict) -> bool:
    important = [
        first_row_value(row, "NGC/IC"),
        first_row_value(row, "Simbad"),
        first_row_value(row, "NED"),
        first_row_value(row, "_RA.icrs", "RA.icrs"),
        first_row_value(row, "_DE.icrs", "DE.icrs"),
    ]
    return any(v != "" for v in important)


def has_real_match_content(row: dict) -> bool:
    return any([
        first_row_value(row, "NGC/IC"),
        first_row_value(row, "Simbad"),
        first_row_value(row, "NED"),
        first_row_value(row, "_RA.icrs", "RA.icrs"),
        first_row_value(row, "_DE.icrs", "DE.icrs"),
    ])


def parse_nullable_int(value: str):
    text = clean_value(value)
    if not text:
        return None
    try:
        return int(text)
    except Exception:
        return None


def hms_dms_to_deg(ra_text: str, dec_text: str):
    def parse_hms(text: str):
        if not text:
            return None
        parts = text.replace("h", ":").replace("m", ":").replace("s", "").split(":")
        parts = [p for p in parts if p != ""]
        if len(parts) != 3:
            return None
        h, m, s = map(float, parts)
        return (h + m / 60.0 + s / 3600.0) * 15.0

    def parse_dms(text: str):
        if not text:
            return None
        sign = -1.0 if text.strip().startswith("-") else 1.0
        cleaned = text.strip().lstrip("+-")
        parts = cleaned.replace("d", ":").replace("m", ":").replace("s", "").split(":")
        parts = [p for p in parts if p != ""]
        if len(parts) != 3:
            return None
        d, m, s = map(float, parts)
        return sign * (d + m / 60.0 + s / 3600.0)

    return parse_hms(ra_text), parse_dms(dec_text)


def parse_tsv(raw_text: str):
    lines = raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    meta = {
        "request_url": "",
        "resource_name": "",
        "resource_title": "",
        "resource_ivoid": "",
        "data_ivoid": "",
        "creator": "",
        "bibcode": "",
        "journal": "",
        "original_date": "",
        "reference_url": "",
        "publication_date": "",
        "rights_uri": "",
        "table_name": "",
        "catalog_code": "",
    }

    columns = []
    units = []
    data_rows = []

    for line in lines:
        if not line.strip():
            continue

        parsed_info = parse_header_value(line)
        if parsed_info:
            k, v = parsed_info
            if k == "request":
                meta["request_url"] = v
            elif k == "reference_url":
                meta["reference_url"] = v
            elif k == "publication_date":
                meta["publication_date"] = v
            elif k == "rights_uri":
                meta["rights_uri"] = v
            continue

        parsed_res = parse_resource_value(line)
        if parsed_res:
            k, v = parsed_res
            kl = k.lower()
            if kl == "resource":
                meta["catalog_code"] = v
            elif kl == "name" and not meta["resource_name"]:
                meta["resource_name"] = v
            elif kl == "title" and not meta["resource_title"]:
                meta["resource_title"] = v
            elif kl == "ivoid" and not meta["resource_ivoid"]:
                meta["resource_ivoid"] = v
            elif kl == "data_ivoid":
                meta["data_ivoid"] = v
            elif kl == "creator":
                meta["creator"] = v
            elif kl == "cites_bibcode":
                meta["bibcode"] = v
            elif kl == "journal":
                meta["journal"] = v
            elif kl == "original_date":
                meta["original_date"] = v
            elif kl == "table":
                meta["table_name"] = v
            continue

        if is_separator_line(line):
            continue

        if line.startswith("Cat\t") or line.startswith("Cat "):
            columns = line.split("\t") if "\t" in line else line.split()
            continue

        if columns and not units:
            maybe_units = line.split("\t") if "\t" in line else line.split()
            unit_tokens = {norm(x) for x in maybe_units if norm(x)}
            if unit_tokens and unit_tokens.issubset({"h:m:s", "d:m:s", "---", "-", "--"}):
                units = maybe_units
                continue

        if columns:
            row = line.split("\t")
            if len(row) < len(columns):
                row.extend([""] * (len(columns) - len(row)))
            row_dict = dict(zip(columns, row))
            cleaned = {k: clean_value(v) for k, v in row_dict.items()}
            if is_real_data_row(cleaned):
                data_rows.append(cleaned)

    if not meta["catalog_code"]:
        meta["catalog_code"] = VIZIER_SOURCE

    return {
        "meta": meta,
        "columns": columns,
        "units": units,
        "rows": data_rows,
        "row_count": len(data_rows),
    }


def choose_best_row(parsed: dict):
    rows = parsed.get("rows", [])
    for row in rows:
        if has_real_match_content(row):
            return row
    return {}


def upsert_vizier(conn, target_row, status: str, error_message: str, parsed, raw_text: str, query_name: str):
    row = choose_best_row(parsed) if parsed else {}

    query_ra_deg = target_row["final_ra_deg"]
    query_dec_deg = target_row["final_dec_deg"]
    position_source = "final_coords"

    ra_icrs_text = first_row_value(row, "_RA.icrs", "RA.icrs")
    dec_icrs_text = first_row_value(row, "_DE.icrs", "DE.icrs")
    match_ra_deg, match_dec_deg = hms_dms_to_deg(ra_icrs_text, dec_icrs_text)
    match_distance_deg = angular_sep_deg(query_ra_deg, query_dec_deg, match_ra_deg, match_dec_deg)
    obs_count = parse_nullable_int(first_row_value(row, "N"))

    match_name = first_row_value(row, "NGC/IC", "Name", "Simbad", "NED")
    match_method = "coords"
    match_confidence = None
    if match_distance_deg is not None:
        if match_distance_deg <= 0.01:
            match_confidence = 0.99
        elif match_distance_deg <= 0.05:
            match_confidence = 0.95
        elif match_distance_deg <= 0.2:
            match_confidence = 0.85
        else:
            match_confidence = 0.50

    conn.execute(
        """
        INSERT INTO target_vizier_resolve (
            target_id, canonical_name, slug, query_name, query_ra_deg, query_dec_deg, position_source,
            match_name, match_ra_deg, match_dec_deg, match_distance_deg, match_method, match_confidence,
            catalog_source, preferred_name, aliases, object_type, object_type_label,
            ra_deg, dec_deg, ra_text, dec_text,
            status, source, error_message, request_url, raw_payload, resolved_at,
            resource_name, resource_title, resource_ivoid, data_ivoid, creator,
            bibcode, journal, original_date, reference_url, publication_date, rights_uri,
            table_name, catalog_code, ngc_ic, ngc_ic_component, ra_b1950, dec_b1950,
            pos_quality, pos_flag, pos_ref, obs_count, comment_text, simbad_ref, ned_ref,
            ra_icrs_text, dec_icrs_text,
            created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, 'vizier', ?, ?, ?, datetime('now'),
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?,
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
            catalog_source=excluded.catalog_source,
            preferred_name=excluded.preferred_name,
            aliases=excluded.aliases,
            object_type=excluded.object_type,
            object_type_label=excluded.object_type_label,
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            ra_text=excluded.ra_text,
            dec_text=excluded.dec_text,
            status=excluded.status,
            source='vizier',
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
            ra_icrs_text=excluded.ra_icrs_text,
            dec_icrs_text=excluded.dec_icrs_text,
            updated_at=datetime('now')
        """,
        (
            target_row["id"],
            norm(target_row["canonical_name"]),
            norm(target_row["slug"]),
            query_name,
            query_ra_deg,
            query_dec_deg,
            position_source,
            match_name,
            match_ra_deg,
            match_dec_deg,
            match_distance_deg,
            match_method,
            match_confidence,
            VIZIER_SOURCE,
            match_name,
            "",
            first_row_value(row, "Cat"),
            "",
            match_ra_deg,
            match_dec_deg,
            ra_icrs_text,
            dec_icrs_text,
            status,
            error_message,
            parsed["meta"]["request_url"] if parsed else "",
            raw_text,
            parsed["meta"]["resource_name"] if parsed else "",
            parsed["meta"]["resource_title"] if parsed else "",
            parsed["meta"]["resource_ivoid"] if parsed else "",
            parsed["meta"]["data_ivoid"] if parsed else "",
            parsed["meta"]["creator"] if parsed else "",
            parsed["meta"]["bibcode"] if parsed else "",
            parsed["meta"]["journal"] if parsed else "",
            parsed["meta"]["original_date"] if parsed else "",
            parsed["meta"]["reference_url"] if parsed else "",
            parsed["meta"]["publication_date"] if parsed else "",
            parsed["meta"]["rights_uri"] if parsed else "",
            parsed["meta"]["table_name"] if parsed else "",
            parsed["meta"]["catalog_code"] if parsed else "",
            first_row_value(row, "NGC/IC"),
            first_row_value(row, "n_NGC/IC"),
            first_row_value(row, "RAB1950"),
            first_row_value(row, "DEB1950"),
            first_row_value(row, "qPos"),
            first_row_value(row, "f_Pos"),
            first_row_value(row, "r_Pos"),
            obs_count,
            first_row_value(row, "Comm"),
            first_row_value(row, "Simbad"),
            first_row_value(row, "NED"),
            ra_icrs_text,
            dec_icrs_text,
        ),
    )


def resolve_one(conn, row):
    query_name = norm(row["final_name"]) or norm(row["display_name"]) or norm(row["canonical_name"])
    ra_deg = row["final_ra_deg"]
    dec_deg = row["final_dec_deg"]
    url = build_url(query_name, ra_deg, dec_deg)

    try:
        raw_text = http_get_text(url)
    except Exception as exc:
        upsert_vizier(conn, row, "error", f"http_error: {exc}", None, "", query_name)
        conn.commit()
        return

    try:
        parsed = parse_tsv(raw_text)
    except Exception as exc:
        upsert_vizier(conn, row, "error", f"parse_error: {exc}", None, raw_text[:2000], query_name)
        conn.commit()
        return

    chosen_row = choose_best_row(parsed)
    if not chosen_row or not has_real_match_content(chosen_row):
        upsert_vizier(conn, row, "unresolved", "no_rows", parsed, raw_text, query_name)
        conn.commit()
        return

    upsert_vizier(conn, row, "resolved", "", parsed, raw_text, query_name)
    conn.commit()


def main() -> int:
    only_new = "--all" not in sys.argv
    limit = 1000

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[idx + 1]))

    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_vizier_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.25)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
