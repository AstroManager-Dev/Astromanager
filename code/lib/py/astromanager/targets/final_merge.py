#!/usr/bin/env python3
import math
import os
import re
import sqlite3
import time

from astromanager.targets.distance_normalizer import normalize_distance_to_ly

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(value) -> str:
    return " ".join(str(value or "").strip().split())


def first_text(*values):
    for value in values:
        text = norm(value)
        if text:
            return text
    return ""


def angular_sep_arcsec(ra1, dec1, ra2, dec2):
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
    return math.degrees(math.acos(cos_sep)) * 3600.0



    try:
        numeric = float(value)
    except Exception:
        return None

    u = norm(unit).lower()

    if u in {"q531", "lichtjahr", "lichtjahre", "light-year", "light-years", "ly"}:
        return numeric

    if u in {"q12129", "parsec", "pc"}:
        return numeric * 3.26156

    if u in {"kiloparsec", "kpc"}:
        return numeric * 3261.56

    if u in {"q3773454", "megaparsec", "mpc"}:
        return numeric * 3261560.0

    if u in {"q1811", "astronomical unit", "astronomische einheit", "au"}:
        return numeric * 0.000015812507409

    return None


def extract_size_arcmin(comment_text):
    text = norm(comment_text)
    if not text:
        return None

    m = re.search(r"size=([<>]?\s*[0-9]+(?:\.[0-9]+)?)", text, flags=re.I)
    if not m:
        return None

    raw = m.group(1).strip()
    raw = raw.lstrip("<>").strip()

    try:
        return float(raw)
    except Exception:
        return None


def select_targets(conn, only_new: bool, limit: int):
    where = ""
    if only_new:
        where = """
        WHERE tf.target_id IS NULL
           OR coalesce(tf.merge_status, 'pending') IN ('pending', 'error', 'partial')
        """

    sql = f"""
    SELECT
        t.id,
        t.canonical_name,
        t.display_name,
        t.slug,
        t.category,
        t.ra_deg,
        t.dec_deg,
        t.coord_status,
        t.coord_source,
        t.coord_ref,
        t.distance_ly AS targets_distance_ly,

        ts.simbad_main_id,
        ts.maintype AS simbad_maintype,
        ts.simbad_otype,
        ts.simbad_ra_deg,
        ts.simbad_dec_deg,
        ts.status AS simbad_status,

        tn.ned_preferred_name,
        tn.ned_objtype,
        tn.ned_ra_deg,
        tn.ned_dec_deg,
        tn.ned_redshift,
        tn.status AS ned_status,

        twn.resolved_name AS wikidata_resolved_name,
        twn.label_de AS wikidata_label_de,
        twn.label_en AS wikidata_label_en,
        twn.wikidata_id,
        twn.status AS wikidata_name_status,

        twm.object_type_label_en AS wikidata_objtype_label_en,
        twm.object_type_label_de AS wikidata_objtype_label_de,
        twm.mag_value AS wikidata_mag_value,
        twm.mag_band AS wikidata_mag_band,
        twm.distance_value AS wikidata_distance_value,
        twm.distance_unit AS wikidata_distance_unit,
        twm.status AS wikidata_meta_status,

        tc.constellation_code,
        tc.constellation_name,
        tc.status AS constellation_status,

        tv.preferred_name AS vizier_preferred_name,
        tv.object_type AS vizier_object_type,
        tv.object_type_label AS vizier_object_type_label,
        tv.magnitude_value AS vizier_mag_value,
        tv.magnitude_band AS vizier_mag_band,
        tv.comment_text AS vizier_comment_text,
        tv.status AS vizier_status,

        tb.ra_deg AS base_ra_deg,
        tb.dec_deg AS base_dec_deg,
        tb.status AS base_status,

        tf.target_id AS final_target_id
    FROM targets t
    LEFT JOIN target_simbad_resolve ts
      ON ts.target_id = t.id
    LEFT JOIN target_ned_resolve tn
      ON tn.target_id = t.id
    LEFT JOIN target_wikidata_name_resolve twn
      ON twn.target_id = t.id
    LEFT JOIN target_wikidata_meta_resolve twm
      ON twm.target_id = t.id
    LEFT JOIN target_constellation_resolve tc
      ON tc.target_id = t.id
    LEFT JOIN target_vizier_resolve tv
      ON tv.target_id = t.id
    LEFT JOIN target_base_resolve tb
      ON tb.target_id = t.id
    LEFT JOIN target_final tf
      ON tf.target_id = t.id
    {where}
    ORDER BY t.id
    LIMIT ?
    """
    return conn.execute(sql, (limit,)).fetchall()


def choose_name(row):
    category = norm(row["category"]).lower()
    canonical = norm(row["canonical_name"])
    display = norm(row["display_name"])

    if category in {"sun", "moon"}:
        return first_text(display, canonical), "category_direct", "category_direct", 1.0

    simbad = norm(row["simbad_main_id"])
    ned = norm(row["ned_preferred_name"])
    wikidata = first_text(
        row["wikidata_resolved_name"],
        row["wikidata_label_en"],
        row["wikidata_label_de"],
    )

    if simbad and ned and simbad.lower() == ned.lower():
        return simbad, "simbad+ned", "simbad+ned", 0.99

    if simbad:
        return simbad, "simbad", "simbad", 0.95

    if ned:
        return ned, "ned", "ned", 0.90

    if wikidata:
        return wikidata, "wikidata", "wikidata", 0.75

    if display:
        return display, "fallback_display", "fallback_display", 0.50

    return canonical, "fallback_canonical", "fallback_canonical", 0.30


def choose_objtype(row):
    category = norm(row["category"]).lower()
    if category == "sun":
        return "Sun", "category_direct"
    if category == "moon":
        return "Moon", "category_direct"

    simbad_type = first_text(row["simbad_maintype"], row["simbad_otype"])
    ned_type = norm(row["ned_objtype"])
    wikidata_type = first_text(
        row["wikidata_objtype_label_en"],
        row["wikidata_objtype_label_de"],
    )
    vizier_type = first_text(row["vizier_object_type_label"], row["vizier_object_type"])

    if simbad_type:
        return simbad_type, "simbad"

    if ned_type:
        return ned_type, "ned"

    if wikidata_type:
        return wikidata_type, "wikidata"

    if vizier_type:
        return vizier_type, "vizier"

    return "", ""


def choose_coords(row):
    if row["ra_deg"] is not None and row["dec_deg"] is not None:
        return row["ra_deg"], row["dec_deg"], "targets"

    if row["base_ra_deg"] is not None and row["base_dec_deg"] is not None:
        return row["base_ra_deg"], row["base_dec_deg"], "target_base_resolve"

    if row["simbad_ra_deg"] is not None and row["simbad_dec_deg"] is not None:
        return row["simbad_ra_deg"], row["simbad_dec_deg"], "simbad"

    if row["ned_ra_deg"] is not None and row["ned_dec_deg"] is not None:
        return row["ned_ra_deg"], row["ned_dec_deg"], "ned"

    return None, None, ""


def choose_distance(row):
    if row["wikidata_distance_value"] is not None:
        return (
            row["wikidata_distance_value"],
            norm(row["wikidata_distance_unit"]),
            "wikidata",
            "wikidata_meta",
        )
    return None, "", "", ""


def choose_magnitude(row):
    if row["wikidata_mag_value"] is not None:
        return row["wikidata_mag_value"], norm(row["wikidata_mag_band"]), "wikidata"

    if row["vizier_mag_value"] is not None:
        return row["vizier_mag_value"], norm(row["vizier_mag_band"]), "vizier"

    return None, "", ""


def choose_constellation(row):
    code = norm(row["constellation_code"])
    name = norm(row["constellation_name"])
    if code or name:
        return code, name, "constellation"
    return "", "", ""


def best_external_sep_arcsec(row, final_ra, final_dec, final_coord_source):
    if final_ra is None or final_dec is None:
        return None

    candidates = []

    if final_coord_source != "simbad" and row["simbad_ra_deg"] is not None and row["simbad_dec_deg"] is not None:
        candidates.append((row["simbad_ra_deg"], row["simbad_dec_deg"]))

    if final_coord_source != "ned" and row["ned_ra_deg"] is not None and row["ned_dec_deg"] is not None:
        candidates.append((row["ned_ra_deg"], row["ned_dec_deg"]))

    if final_coord_source != "target_base_resolve" and row["base_ra_deg"] is not None and row["base_dec_deg"] is not None:
        candidates.append((row["base_ra_deg"], row["base_dec_deg"]))

    best = None
    for ra2, dec2 in candidates:
        sep = angular_sep_arcsec(final_ra, final_dec, ra2, dec2)
        if sep is None:
            continue
        if best is None or sep < best:
            best = sep
    return best


def build_source_summary(name_source, objtype_source, coord_source, distance_source, mag_source, constellation_source):
    parts = []
    if name_source:
        parts.append(f"name:{name_source}")
    if objtype_source:
        parts.append(f"objtype:{objtype_source}")
    if coord_source:
        parts.append(f"coords:{coord_source}")
    if distance_source:
        parts.append(f"distance:{distance_source}")
    if mag_source:
        parts.append(f"mag:{mag_source}")
    if constellation_source:
        parts.append(f"constellation:{constellation_source}")
    return ";".join(parts)


def merge_status(row, final_name, final_ra, final_dec, final_objtype):
    category = norm(row["category"]).lower()

    if category in {"sun", "moon"}:
        if final_name and final_objtype:
            return "resolved"
        return "partial"

    if final_name and final_ra is not None and final_dec is not None and final_objtype:
        return "resolved"
    if final_name or final_ra is not None or final_dec is not None or final_objtype:
        return "partial"
    return "pending"


def merge_notes(row, final_coord_source):
    notes = []

    if row["vizier_status"] == "unresolved":
        notes.append("vizier_unresolved")

    if row["ned_status"] not in ("resolved", "", None):
        notes.append(f"ned_{norm(row['ned_status']).lower()}")

    if row["simbad_status"] not in ("resolved", "", None):
        notes.append(f"simbad_{norm(row['simbad_status']).lower()}")

    if final_coord_source == "targets" and row["simbad_ra_deg"] is not None and row["simbad_dec_deg"] is not None:
        sep = angular_sep_arcsec(row["ra_deg"], row["dec_deg"], row["simbad_ra_deg"], row["simbad_dec_deg"])
        if sep is not None and sep > 30:
            notes.append(f"coord_vs_simbad>{sep:.2f}arcsec")

    return ";".join(notes)


def upsert_final(conn, row):
    final_name, final_name_source, identity_method, identity_confidence = choose_name(row)
    final_objtype, final_objtype_source = choose_objtype(row)
    final_ra, final_dec, final_coord_source = choose_coords(row)
    final_distance_value, final_distance_unit, distance_source, distance_ref = choose_distance(row)
    mag_value, mag_band, mag_source = choose_magnitude(row)
    constellation_code, constellation_name, constellation_source = choose_constellation(row)

    distance_ly = None
    if final_distance_value is not None:
        distance_ly, _distance_norm_unit = normalize_distance_to_ly(
            final_distance_value,
            final_distance_unit,
            "",
            "",
        )

    if distance_ly is None and row["targets_distance_ly"] is not None:
        distance_ly = row["targets_distance_ly"]

    if distance_ly is not None:
        final_distance_value = distance_ly
        final_distance_unit = "Lichtjahr"
        distance_ref = "harmonized_ly"

    coord_match_sep_arcsec = best_external_sep_arcsec(row, final_ra, final_dec, final_coord_source)
    angular_size_arcmin = extract_size_arcmin(row["vizier_comment_text"])

    final_source_summary = build_source_summary(
        final_name_source,
        final_objtype_source,
        final_coord_source,
        distance_source,
        mag_source,
        constellation_source,
    )
    notes = merge_notes(row, final_coord_source)
    status = merge_status(row, final_name, final_ra, final_dec, final_objtype)

    conn.execute(
        """
        INSERT INTO target_final (
            target_id,
            canonical_name,
            display_name,
            slug,
            category,
            final_name,
            final_name_source,
            final_objtype,
            final_objtype_source,
            final_ra_deg,
            final_dec_deg,
            final_coord_source,
            final_distance_value,
            final_distance_unit,
            distance_ly,
            distance_source,
            distance_ref,
            mag_value,
            mag_band,
            mag_source,
            constellation_code,
            constellation_name,
            constellation_source,
            identity_method,
            identity_confidence,
            coord_match_sep_arcsec,
            angular_size_arcmin,
            final_source_summary,
            merge_status,
            merge_notes,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            datetime('now'), datetime('now')
        )
        ON CONFLICT(target_id) DO UPDATE SET
            canonical_name=excluded.canonical_name,
            display_name=excluded.display_name,
            slug=excluded.slug,
            category=excluded.category,
            final_name=excluded.final_name,
            final_name_source=excluded.final_name_source,
            final_objtype=excluded.final_objtype,
            final_objtype_source=excluded.final_objtype_source,
            final_ra_deg=excluded.final_ra_deg,
            final_dec_deg=excluded.final_dec_deg,
            final_coord_source=excluded.final_coord_source,
            final_distance_value=excluded.final_distance_value,
            final_distance_unit=excluded.final_distance_unit,
            distance_ly=excluded.distance_ly,
            distance_source=excluded.distance_source,
            distance_ref=excluded.distance_ref,
            mag_value=excluded.mag_value,
            mag_band=excluded.mag_band,
            mag_source=excluded.mag_source,
            constellation_code=excluded.constellation_code,
            constellation_name=excluded.constellation_name,
            constellation_source=excluded.constellation_source,
            identity_method=excluded.identity_method,
            identity_confidence=excluded.identity_confidence,
            coord_match_sep_arcsec=excluded.coord_match_sep_arcsec,
            angular_size_arcmin=excluded.angular_size_arcmin,
            final_source_summary=excluded.final_source_summary,
            merge_status=excluded.merge_status,
            merge_notes=excluded.merge_notes,
            updated_at=datetime('now')
        """,
        (
            row["id"],
            norm(row["canonical_name"]),
            norm(row["display_name"]),
            norm(row["slug"]),
            norm(row["category"]),
            final_name,
            final_name_source,
            final_objtype,
            final_objtype_source,
            final_ra,
            final_dec,
            final_coord_source,
            final_distance_value,
            final_distance_unit,
            distance_ly,
            distance_source,
            distance_ref,
            mag_value,
            mag_band,
            mag_source,
            constellation_code,
            constellation_name,
            constellation_source,
            identity_method,
            identity_confidence,
            coord_match_sep_arcsec,
            angular_size_arcmin,
            final_source_summary,
            status,
            notes,
        ),
    )


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_final_merge={len(rows)}")
        for row in rows:
            print(f"merging id={row['id']} canonical_name={row['canonical_name']}")
            upsert_final(conn, row)
            conn.commit()
            time.sleep(0.03)
    finally:
        conn.close()
    return 0
