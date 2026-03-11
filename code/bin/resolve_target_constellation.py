#!/usr/bin/env python3
import os
import sqlite3

import astropy.units as u
from astropy.coordinates import SkyCoord

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT
              t.id,
              t.canonical_name,
              t.slug,
              t.category,
              tcr.query_name,
              tcr.query_ra_deg,
              tcr.query_dec_deg,
              tcr.position_source,
              tbr.ra_deg AS base_ra_deg,
              tbr.dec_deg AS base_dec_deg
            FROM targets t
            LEFT JOIN target_constellation_resolve tcr
              ON tcr.target_id = t.id
            LEFT JOIN target_base_resolve tbr
              ON tbr.target_id = t.id
            ORDER BY t.id
            """
        ).fetchall()

        print(f"targets_to_constellation_resolve={len(rows)}")

        for row in rows:
            canonical_name = row["canonical_name"]
            category = (row["category"] or "").strip().lower()

            ra_deg = row["base_ra_deg"]
            dec_deg = row["base_dec_deg"]
            position_source = "target_base_resolve" if ra_deg is not None and dec_deg is not None else ""
            query_name = row["query_name"] or canonical_name or row["slug"] or ""
            match_name = query_name
            match_ra_deg = ra_deg
            match_dec_deg = dec_deg

            if category in ("sun", "moon"):
                status = "skipped"
                error_message = f"system_target_{category}_not_supported_yet"
                constellation_name = ""
                constellation_code = ""
                source = "astropy_get_constellation"
                match_method = "category_skip"
                match_confidence = 1.0
                match_distance_deg = 0.0 if ra_deg is not None and dec_deg is not None else None
            elif ra_deg is None or dec_deg is None:
                status = "pending"
                error_message = "missing_base_coordinates"
                constellation_name = ""
                constellation_code = ""
                source = "astropy_get_constellation"
                match_method = "missing_base_coordinates"
                match_confidence = None
                match_distance_deg = None
                match_ra_deg = None
                match_dec_deg = None
            else:
                try:
                    coord = SkyCoord(ra=float(ra_deg) * u.deg, dec=float(dec_deg) * u.deg, frame="icrs")
                    constellation_name = coord.get_constellation(short_name=False)
                    constellation_code = coord.get_constellation(short_name=True)
                    status = "resolved"
                    error_message = None
                    source = "astropy_get_constellation"
                    match_method = "ra_dec_to_constellation"
                    match_confidence = 1.0
                    match_distance_deg = 0.0
                except Exception as exc:
                    constellation_name = ""
                    constellation_code = ""
                    status = "error"
                    error_message = str(exc)
                    source = "astropy_get_constellation"
                    match_method = "exception"
                    match_confidence = None
                    match_distance_deg = None

            conn.execute(
                """
                INSERT INTO target_constellation_resolve (
                  target_id,
                  canonical_name,
                  slug,
                  constellation_name,
                  status,
                  source,
                  error_message,
                  resolved_at,
                  created_at,
                  updated_at,
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
                  constellation_code
                )
                VALUES (
                  ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'),
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(target_id) DO UPDATE SET
                  canonical_name=excluded.canonical_name,
                  slug=excluded.slug,
                  constellation_name=excluded.constellation_name,
                  status=excluded.status,
                  source=excluded.source,
                  error_message=excluded.error_message,
                  resolved_at=datetime('now'),
                  updated_at=datetime('now'),
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
                  constellation_code=excluded.constellation_code
                """,
                (
                    row["id"],
                    canonical_name,
                    row["slug"],
                    constellation_name,
                    status,
                    source,
                    error_message,
                    query_name,
                    ra_deg,
                    dec_deg,
                    position_source,
                    match_name,
                    match_ra_deg,
                    match_dec_deg,
                    match_distance_deg,
                    match_method,
                    match_confidence,
                    constellation_code,
                ),
            )

            print(
                f"resolved id={row['id']} canonical_name={canonical_name} "
                f"status={status} constellation_name={constellation_name} "
                f"constellation_code={constellation_code} position_source={position_source}"
            )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
