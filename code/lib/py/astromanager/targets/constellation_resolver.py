#!/usr/bin/env python3
import os
import sqlite3
import time

from astropy.coordinates import SkyCoord
import astropy.units as u

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(v) -> str:
    return " ".join(str(v or "").strip().split())


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
            t.category,
            t.ra_deg AS target_ra_deg,
            t.dec_deg AS target_dec_deg,
            b.ra_deg AS base_ra_deg,
            b.dec_deg AS base_dec_deg,
            c.target_id AS constellation_target_id,
            c.status AS constellation_status
        FROM targets t
        LEFT JOIN target_base_resolve b
          ON b.target_id = t.id
        LEFT JOIN target_constellation_resolve c
          ON c.target_id = t.id
        WHERE
          c.target_id IS NULL
          OR coalesce(c.status, 'pending') IN ('pending', 'error', 'unresolved')
        ORDER BY t.id
        LIMIT ?
        """
    else:
        sql = """
        SELECT
            t.id,
            t.canonical_name,
            t.category,
            t.ra_deg AS target_ra_deg,
            t.dec_deg AS target_dec_deg,
            b.ra_deg AS base_ra_deg,
            b.dec_deg AS base_dec_deg,
            c.target_id AS constellation_target_id,
            c.status AS constellation_status
        FROM targets t
        LEFT JOIN target_base_resolve b
          ON b.target_id = t.id
        LEFT JOIN target_constellation_resolve c
          ON c.target_id = t.id
        ORDER BY t.id
        LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def upsert_result(
    conn,
    row,
    ra_deg,
    dec_deg,
    constellation_name,
    constellation_code,
    status,
    source,
    error_message="",
):
    conn.execute(
        """
        INSERT INTO target_constellation_resolve (
            target_id,
            ra_deg,
            dec_deg,
            constellation_name,
            constellation_code,
            status,
            source,
            error_message,
            resolved_at,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now')
        )
        ON CONFLICT(target_id) DO UPDATE SET
            ra_deg=excluded.ra_deg,
            dec_deg=excluded.dec_deg,
            constellation_name=excluded.constellation_name,
            constellation_code=excluded.constellation_code,
            status=excluded.status,
            source=excluded.source,
            error_message=excluded.error_message,
            resolved_at=datetime('now'),
            updated_at=datetime('now')
        """,
        (
            row["id"],
            ra_deg,
            dec_deg,
            constellation_name,
            constellation_code,
            status,
            source,
            error_message,
        ),
    )


def resolve_one(conn, row):
    if is_system_target(row):
        upsert_result(
            conn,
            row,
            None,
            None,
            "",
            "",
            "skipped",
            "constellation",
            "",
        )
        conn.commit()
        return

    ra_deg = row["target_ra_deg"]
    dec_deg = row["target_dec_deg"]
    source = "targets"

    if ra_deg is None or dec_deg is None:
        ra_deg = row["base_ra_deg"]
        dec_deg = row["base_dec_deg"]
        source = "target_base_resolve"

    if ra_deg is None or dec_deg is None:
        upsert_result(
            conn,
            row,
            None,
            None,
            "",
            "",
            "pending",
            source,
            "missing coordinates",
        )
        conn.commit()
        return

    try:
        coord = SkyCoord(ra=float(ra_deg) * u.deg, dec=float(dec_deg) * u.deg, frame="icrs")
        code = coord.get_constellation(short_name=True)
        name = coord.get_constellation(short_name=False)

        upsert_result(
            conn,
            row,
            float(ra_deg),
            float(dec_deg),
            norm(name),
            norm(code),
            "resolved",
            source,
            "",
        )
        conn.commit()
    except Exception as e:
        upsert_result(
            conn,
            row,
            ra_deg,
            dec_deg,
            "",
            "",
            "error",
            source,
            str(e),
        )
        conn.commit()


def run(only_new: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_constellation_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.05)
    finally:
        conn.close()
    return 0
