#!/usr/bin/env python3
import os
import sqlite3
import sys
import time
import urllib.parse

APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY_ROOT = os.path.join(APP_ROOT, "lib", "py")
if LIB_PY_ROOT not in sys.path:
    sys.path.insert(0, LIB_PY_ROOT)

from astromanager.targets.image_resolver_rules import choose_frame_deg, choose_query_name, choose_skyview_survey
from astromanager.targets.image_validation import fetch_image_validation

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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


def upsert_result(conn, row, query_name, survey, image_url, fits_url, status, error_message):
    store_image_url = image_url if status == 'resolved' else ''
    store_fits_url = fits_url if status == 'resolved' else ''
    conn.execute(
        """
        INSERT INTO target_skyview_resolve (
            target_id, canonical_name, slug, query_name, survey, position_source,
            ra_deg, dec_deg, image_url, fits_url, status, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
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
            status=excluded.status,
            error_message=excluded.error_message,
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
            store_image_url,
            store_fits_url,
            status,
            error_message,
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
            query_name = choose_query_name(row)
            ra = row["final_ra_deg"]
            dec = row["final_dec_deg"]
            pos = f"{ra},{dec}"
            survey = choose_skyview_survey(row)
            size_deg = choose_frame_deg(row, 'skyview')

            params_img = urllib.parse.urlencode({
                "Position": pos,
                "Survey": survey,
                "Return": "PNG",
                "Sampler": "Clip",
                "Pixels": "600",
                "Size": f"{size_deg:.4f}",
            })
            params_fits = urllib.parse.urlencode({
                "Position": pos,
                "Survey": survey,
                "Return": "FITS",
                "Sampler": "Clip",
                "Pixels": "600",
                "Size": f"{size_deg:.4f}",
            })

            image_url = f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?{params_img}"
            fits_url = f"https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?{params_fits}"

            try:
                validation = fetch_image_validation(image_url)
                status = 'resolved' if validation.get('ok') else 'no_data'
                error_message = validation.get('error') or None
            except Exception as exc:
                status = 'error'
                error_message = str(exc)

            upsert_result(conn, row, query_name, survey, image_url, fits_url, status, error_message)
            print(
                f"{status} id={row['id']} canonical_name={row['canonical_name']} survey={survey} size_deg={size_deg:.4f}"
                + (f" error={error_message}" if error_message else "")
            )
            time.sleep(0.05)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
