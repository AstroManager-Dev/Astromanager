#!/usr/bin/env python3
import os
import sqlite3
import sys
import time

APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY_ROOT = os.path.join(APP_ROOT, "lib", "py")
if LIB_PY_ROOT not in sys.path:
    sys.path.insert(0, LIB_PY_ROOT)

from astromanager.paths import TARGET_NAME_PARSER_MODULE  # noqa: E402
from astromanager.targets.name_parser import choose_final_name  # noqa: E402

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def pick(*vals):
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str):
            if v.strip() != "":
                return v.strip()
        else:
            return v
    return None


def normalize_distance_to_ly(value, unit):
    if value is None:
        return None, ""

    u = (unit or "").strip().lower()

    if u in ("lichtjahr", "lichtjahre", "light-year", "light-years", "ly"):
        return float(value), "Lichtjahr"
    if u in ("parsec", "pc"):
        return float(value) * 3.26156, "Lichtjahr"
    if u in ("kiloparsec", "kpc"):
        return float(value) * 3261.56, "Lichtjahr"
    if u in ("megaparsec", "mpc"):
        return float(value) * 3261560.0, "Lichtjahr"

    return float(value), unit or ""


def select_targets(conn, limit: int):
    return conn.execute("""
        select *
        from targets
        order by id
        limit ?
    """, (limit,)).fetchall()


def merge_one(conn, row):
    final_name = choose_final_name(row)

    final_objtype = pick(
        row["object_type_label_de"],
        row["object_type_label_en"],
        row["ned_objtype"],
        row["simbad_otype"],
    )

    final_ra_deg = pick(
        row["simbad_ra_deg"],
        row["ned_ra_deg"],
        row["ra_deg"],
    )

    final_dec_deg = pick(
        row["simbad_dec_deg"],
        row["ned_dec_deg"],
        row["dec_deg"],
    )

    raw_distance_value = pick(row["distance_value"])
    raw_distance_unit = pick(
        row["distance_unit_label_de"],
        row["distance_unit_label_en"],
        row["distance_unit"],
    )

    final_distance_value, final_distance_unit = normalize_distance_to_ly(
        raw_distance_value,
        raw_distance_unit,
    )

    source_summary = "name=Wikidata|coords=SIMBAD>NED>Sesame|objtype=Wikidata>NED>SIMBAD|distance=Wikidata"

    category_l = (row["category"] or "").strip().lower()

    if category_l in ("sun", "moon"):
        identity_method = "fixed_system_target"
        identity_confidence = 1.0
    elif final_name and final_ra_deg is not None and final_dec_deg is not None:
        identity_method = "name+coord"
        identity_confidence = 0.95
    elif final_name:
        identity_method = "name"
        identity_confidence = 0.75
    else:
        identity_method = "fallback"
        identity_confidence = 0.5

    distance_ly = final_distance_value if (final_distance_unit or "").strip().lower() == "lichtjahr" else None

    if row["distance_value"] is not None:
        distance_source = "wikidata"
        distance_ref = row["wikidata_id"] or ""
    elif row["ned_redshift"] is not None:
        distance_source = "ned"
        distance_ref = row["ned_preferred_name"] or ""
    else:
        distance_source = ""
        distance_ref = ""

    conn.execute("""
        update targets
           set final_name=?,
               final_objtype=?,
               final_ra_deg=?,
               final_dec_deg=?,
               final_distance_value=?,
               final_distance_unit=?,
               final_source_summary=?,
               distance_ly=?,
               distance_source=?,
               distance_ref=?,
               identity_method=?,
               identity_confidence=?,
               updated_at=datetime('now')
         where id=?
    """, (
        final_name or "",
        final_objtype or "",
        final_ra_deg,
        final_dec_deg,
        final_distance_value,
        final_distance_unit or "",
        source_summary,
        distance_ly,
        distance_source,
        distance_ref,
        identity_method,
        identity_confidence,
        row["id"],
    ))
    conn.commit()


def main():
    limit = 1000
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[i + 1]))

    print(f"target_name_parser_module={TARGET_NAME_PARSER_MODULE}")

    conn = db()
    try:
        rows = select_targets(conn, limit)
        print(f"targets_to_merge={len(rows)}")
        for row in rows:
            print(f"merging id={row['id']} canonical_name={row['canonical_name']}")
            merge_one(conn, row)
            time.sleep(0.05)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
