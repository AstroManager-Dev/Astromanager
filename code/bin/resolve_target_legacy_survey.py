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

from astromanager.targets.image_resolver_rules import (
    LEGACY_DEFAULT_BANDS,
    LEGACY_DEFAULT_MAX_SIZE,
    LEGACY_DEFAULT_PIXSCALE,
    choose_frame_deg,
    choose_legacy_layer,
    choose_query_name,
    legacy_size_px_from_frame,
)

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
LEGACY_BASE = os.environ.get("LEGACY_SURVEY_BASE", "https://www.legacysurvey.org/viewer")
PIX_SCALE = float(os.environ.get("LEGACY_SURVEY_PIXSCALE", str(LEGACY_DEFAULT_PIXSCALE)))
MAX_SIZE_PX = int(os.environ.get("LEGACY_SURVEY_MAX_SIZE", str(LEGACY_DEFAULT_MAX_SIZE)))
DEFAULT_BANDS = os.environ.get("LEGACY_SURVEY_BANDS", LEGACY_DEFAULT_BANDS)


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


def upsert(conn, row, query_name, layer, bands, frame_deg, size_px, image_url, fits_url, viewer_url):
    conn.execute(
        """
        INSERT INTO target_legacy_survey_resolve (
            target_id, canonical_name, slug, query_name, layer, bands, pixscale_arcsec,
            size_px, frame_deg, position_source, ra_deg, dec_deg, image_url, fits_url,
            viewer_url, status, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'resolved', NULL, datetime('now'), datetime('now'))
        ON CONFLICT(target_id) DO UPDATE SET
            canonical_name=excluded.canonical_name,
            slug=excluded.slug,
            query_name=excluded.query_name,
            layer=excluded.layer,
            bands=excluded.bands,
            pixscale_arcsec=excluded.pixscale_arcsec,
            size_px=excluded.size_px,
            frame_deg=excluded.frame_deg,
            position_source=excluded.position_source,
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            image_url=excluded.image_url,
            fits_url=excluded.fits_url,
            viewer_url=excluded.viewer_url,
            status='resolved',
            error_message=NULL,
            updated_at=datetime('now')
        """,
        (
            row['id'], row['canonical_name'] if 'canonical_name' in row.keys() else '', row['slug'] if 'slug' in row.keys() else '',
            query_name, layer, bands, PIX_SCALE, size_px, frame_deg, 'final_coords', row['final_ra_deg'], row['final_dec_deg'],
            image_url, fits_url, viewer_url,
        ),
    )
    conn.commit()


def main():
    limit = 1000
    if '--limit' in sys.argv:
        i = sys.argv.index('--limit')
        if i + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[i + 1]))

    conn = db()
    try:
        rows = select_targets(conn, limit)
        print(f"targets_to_legacy_survey_resolve={len(rows)}")
        for row in rows:
            query_name = choose_query_name(row)
            ra = float(row['final_ra_deg'])
            dec = float(row['final_dec_deg'])
            layer = choose_legacy_layer(dec)
            frame_deg = choose_frame_deg(row, 'legacy')
            size_px = legacy_size_px_from_frame(frame_deg, PIX_SCALE, MAX_SIZE_PX)
            common = {
                'ra': f"{ra:.6f}",
                'dec': f"{dec:.6f}",
                'layer': layer,
                'pixscale': f"{PIX_SCALE:.3f}",
                'size': str(size_px),
            }
            image_url = f"{LEGACY_BASE}/jpeg-cutout?" + urllib.parse.urlencode(common)
            fits_params = dict(common)
            fits_params['bands'] = DEFAULT_BANDS
            fits_url = f"{LEGACY_BASE}/fits-cutout?" + urllib.parse.urlencode(fits_params)
            viewer_url = f"{LEGACY_BASE}?" + urllib.parse.urlencode({
                'ra': f"{ra:.6f}", 'dec': f"{dec:.6f}", 'layer': layer, 'zoom': '13'
            })
            upsert(conn, row, query_name, layer, DEFAULT_BANDS, frame_deg, size_px, image_url, fits_url, viewer_url)
            print(f"resolved id={row['id']} canonical_name={row['canonical_name']} layer={layer} frame_deg={frame_deg:.4f} size_px={size_px}")
            time.sleep(0.05)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
