#!/usr/bin/env python3
import os
import sqlite3
import sys
import time
import urllib.parse

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(v):
    return " ".join((v or "").strip().split())


def choose_name(row):
    for key in ("final_name", "display_name", "label_de", "label_en", "canonical_name"):
        if key in row.keys():
            v = norm(row[key])
            if v:
                return v
    return ""


def select_targets(conn, limit: int):
    sql = """
    SELECT *
    FROM targets
    WHERE lower(coalesce(category,'')) not in ('sun','moon')
      AND lower(coalesce(canonical_name,'')) not in ('sun','moon')
      AND final_ra_deg IS NOT NULL
      AND final_dec_deg IS NOT NULL
    ORDER BY id
    LIMIT ?
    """
    return conn.execute(sql, (limit,)).fetchall()


def upsert(conn, row, query_name, survey, image_url, fits_url):
    conn.execute(
        """
        INSERT INTO target_skyview_resolve (
            target_id, canonical_name, slug, query_name, survey, position_source,
            ra_deg, dec_deg, image_url, fits_url, status, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'resolved', NULL, datetime('now'), datetime('now'))
        ON CONFLICT(target_id) DO UPDATE SET
            canonical_name=excluded.canonical_name,
            slug=excluded.slug,
            query_name=excluded.query_name,
            survey=excluded.survey,
            position_source=excluded.position_source,
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            image_url=excluded.image_url,
            fits_url=excluded.fits_url,
            status='resolved',
            error_message=NULL,
            updated_at=datetime('now')
        """,
        (
            row["id"],
            row["canonical_name"] if "canonical_name" in row.keys() else "",
            row["slug"] if "slug" in row.keys() else "",
            query_name,
            survey,
            "final_coords",
            row["final_ra_deg"],
            row["final_dec_deg"],
            image_url,
            fits_url,
        ),
    )
    conn.commit()


def main():
    limit = 1000
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[i + 1]))

    conn = db()
    try:
        rows = select_targets(conn, limit)
        print(f"targets_to_skyview_resolve={len(rows)}")
        for row in rows:
            name = choose_name(row)
            ra = row["final_ra_deg"]
            dec = row["final_dec_deg"]
            pos = f"{ra},{dec}"
            survey = "DSS2 Color"

            params_img = urllib.parse.urlencode({
                "Position": pos,
                "Survey": survey,
                "Return": "PNG",
                "Sampler": "Clip",
                "Pixels": "600",
                "Size": "0.35",
            })
            params_fits = urllib.parse.urlencode({
                "Position": pos,
                "Survey": survey,
                "Return": "FITS",
                "Sampler": "Clip",
                "Pixels": "600",
                "Size": "0.35",
            })

            image_url = f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?{params_img}"
            fits_url = f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?{params_fits}"

            upsert(conn, row, name, survey, image_url, fits_url)
            print(f"resolved id={row['id']} canonical_name={row['canonical_name']}")
            time.sleep(0.05)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
