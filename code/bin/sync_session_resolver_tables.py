#!/usr/bin/env python3
import sqlite3
import sys

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "/runtime/pipeline.db"
MODE = sys.argv[2] if len(sys.argv) > 2 else ""

if MODE not in {"platesolve", "targetresolve"}:
    raise SystemExit("usage: sync_session_resolver_tables.py /runtime/pipeline.db <platesolve|targetresolve>")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def table_cols(table: str) -> set[str]:
    return {r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}

def upsert(table: str, key_col: str, key_val, data: dict):
    cols = table_cols(table)
    payload = {k: v for k, v in data.items() if k in cols}
    payload[key_col] = key_val
    if "updated_at" in cols and "updated_at" not in payload:
        payload["updated_at"] = None
    existing = cur.execute(f"SELECT 1 FROM {table} WHERE {key_col}=?", (key_val,)).fetchone()
    if existing:
        sets = []
        vals = []
        for k, v in payload.items():
            if k == key_col:
                continue
            if k == "updated_at":
                sets.append("updated_at=datetime('now')")
            else:
                sets.append(f"{k}=?")
                vals.append(v)
        if sets:
            vals.append(key_val)
            cur.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE {key_col}=?", vals)
    else:
        insert_cols = []
        insert_vals = []
        vals = []
        for k, v in payload.items():
            insert_cols.append(k)
            if k == "updated_at":
                insert_vals.append("datetime('now')")
            else:
                insert_vals.append("?")
                vals.append(v)
        if "created_at" in cols and "created_at" not in payload:
            insert_cols.append("created_at")
            insert_vals.append("datetime('now')")
        cur.execute(
            f"INSERT INTO {table} ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})",
            vals,
        )

if MODE == "platesolve":
    rows = cur.execute("""
        SELECT
          id,
          session_key,
          target,
          platesolve_status,
          platesolve_attempts,
          platesolve_last_at,
          platesolve_reference_path,
          solve_ra_deg,
          solve_dec_deg,
          solve_fov_x_deg,
          solve_fov_y_deg,
          solve_rotation_deg,
          footprint_radius_deg,
          corner_ul_ra_deg,
          corner_ul_dec_deg,
          corner_ur_ra_deg,
          corner_ur_dec_deg,
          corner_lr_ra_deg,
          corner_lr_dec_deg,
          corner_ll_ra_deg,
          corner_ll_dec_deg,
          solve_engine,
          solve_message,
          solve_pass
        FROM sessions
        WHERE platesolve_status IS NOT NULL
    """).fetchall()

    for row in rows:
        upsert("session_platesolve_resolve", "session_id", row["id"], {
            "session_key": row["session_key"],
            "target": row["target"],
            "platesolve_status": row["platesolve_status"],
            "platesolve_attempts": row["platesolve_attempts"],
            "platesolve_last_at": row["platesolve_last_at"],
            "platesolve_reference_path": row["platesolve_reference_path"],
            "solve_ra_deg": row["solve_ra_deg"],
            "solve_dec_deg": row["solve_dec_deg"],
            "solve_fov_x_deg": row["solve_fov_x_deg"],
            "solve_fov_y_deg": row["solve_fov_y_deg"],
            "solve_rotation_deg": row["solve_rotation_deg"],
            "footprint_radius_deg": row["footprint_radius_deg"],
            "corner_ul_ra_deg": row["corner_ul_ra_deg"],
            "corner_ul_dec_deg": row["corner_ul_dec_deg"],
            "corner_ur_ra_deg": row["corner_ur_ra_deg"],
            "corner_ur_dec_deg": row["corner_ur_dec_deg"],
            "corner_lr_ra_deg": row["corner_lr_ra_deg"],
            "corner_lr_dec_deg": row["corner_lr_dec_deg"],
            "corner_ll_ra_deg": row["corner_ll_ra_deg"],
            "corner_ll_dec_deg": row["corner_ll_dec_deg"],
            "solve_engine": row["solve_engine"],
            "solve_message": row["solve_message"],
            "solve_pass": row["solve_pass"],
        })

elif MODE == "targetresolve":
    rows = cur.execute("""
        SELECT
          id,
          session_key,
          target,
          target_final,
          target_final_source,
          target_strategy,
          field_object_count,
          requested_target_found,
          target_conflict_flag,
          target_conflict_note
        FROM sessions
        WHERE platesolve_status='solved'
    """).fetchall()

    for row in rows:
        upsert("session_target_resolve", "session_id", row["id"], {
            "session_key": row["session_key"],
            "target_raw": row["target"],
            "target_final": row["target_final"],
            "target_final_source": row["target_final_source"],
            "target_strategy": row["target_strategy"],
            "field_object_count": row["field_object_count"],
            "requested_target_found": row["requested_target_found"],
            "target_conflict_flag": row["target_conflict_flag"],
            "target_conflict_note": row["target_conflict_note"],
        })

    cur.execute("DELETE FROM session_target_resolve_item")

    item_rows = cur.execute("""
        SELECT
          st.session_id,
          st.target_id,
          st.target_name,
          st.object_type,
          st.source,
          st.is_requested_target,
          st.is_primary,
          st.is_major,
          st.priority_rank,
          st.score,
          st.distance_to_center_deg,
          st.in_frame_fraction,
          st.angular_size_arcmin,
          st.ra_deg,
          st.dec_deg,
          st.notes
        FROM session_targets st
    """).fetchall()

    for row in item_rows:
        cur.execute("""
            INSERT INTO session_target_resolve_item (
              session_id, target_id, target_name, object_type, source,
              is_requested_target, is_primary, is_major, priority_rank, score,
              distance_to_center_deg, in_frame_fraction, angular_size_arcmin,
              ra_deg, dec_deg, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            row["session_id"], row["target_id"], row["target_name"], row["object_type"], row["source"],
            row["is_requested_target"], row["is_primary"], row["is_major"], row["priority_rank"], row["score"],
            row["distance_to_center_deg"], row["in_frame_fraction"], row["angular_size_arcmin"],
            row["ra_deg"], row["dec_deg"], row["notes"],
        ))

conn.commit()
conn.close()
print(f"OK mode={MODE}")
