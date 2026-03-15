#!/usr/bin/env python3
import sqlite3

MODES = {
    "base": "target_base_resolve",
    "wikidata_name": "target_wikidata_name_resolve",
    "wikidata_meta": "target_wikidata_meta_resolve",
    "simbad": "target_simbad_resolve",
    "ned": "target_ned_resolve",
    "constellation": "target_constellation_resolve",
    "nasa": "target_nasa_resolve",
    "legacy": "target_legacy_survey_resolve",
    "skyview": "target_skyview_resolve",
    "irsa": "target_irsa_resolve",
    "sesame": "target_sesame_resolve",
    "vizier": "target_vizier_resolve",
    "ssodnet": "target_ssodnet_resolve",
}


def open_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(cur, table: str) -> bool:
    row = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def table_cols(cur, table: str) -> set[str]:
    return {r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}


def row_has(row: sqlite3.Row, key: str) -> bool:
    return key in row.keys()


def val(row: sqlite3.Row, key: str, default=None):
    if row_has(row, key):
        return row[key]
    return default


def first_nonempty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip() != "":
                return value.strip()
        else:
            return value
    return None


def upsert(cur, table: str, key_col: str, key_val, data: dict):
    cols = table_cols(cur, table)
    payload = {k: v for k, v in data.items() if k in cols}
    payload[key_col] = key_val

    existing = cur.execute(
        f"SELECT 1 FROM {table} WHERE {key_col}=?",
        (key_val,),
    ).fetchone()

    if existing:
        sets = []
        vals_out = []
        for k, v in payload.items():
            if k == key_col:
                continue
            if k == "updated_at":
                sets.append("updated_at=datetime('now')")
            else:
                sets.append(f"{k}=?")
                vals_out.append(v)

        if "updated_at" in cols and "updated_at" not in payload:
            sets.append("updated_at=datetime('now')")

        if sets:
            vals_out.append(key_val)
            cur.execute(
                f"UPDATE {table} SET {', '.join(sets)} WHERE {key_col}=?",
                vals_out,
            )
        return

    insert_cols = []
    insert_vals = []
    vals_out = []

    for k, v in payload.items():
        insert_cols.append(k)
        if k in ("created_at", "updated_at"):
            insert_vals.append("datetime('now')")
        else:
            insert_vals.append("?")
            vals_out.append(v)

    if "created_at" in cols and "created_at" not in payload:
        insert_cols.append("created_at")
        insert_vals.append("datetime('now')")

    if "updated_at" in cols and "updated_at" not in payload:
        insert_cols.append("updated_at")
        insert_vals.append("datetime('now')")

    cur.execute(
        f"INSERT INTO {table} ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})",
        vals_out,
    )


def build_common(row):
    return {
        "canonical_name": val(row, "canonical_name"),
        "slug": val(row, "slug"),
    }


def build_mode_payload(mode: str, row):
    common = build_common(row)

    if mode == "base":
        base_ra = val(row, "ra_deg")
        base_dec = val(row, "dec_deg")
        query_name = first_nonempty(
            val(row, "canonical_name"),
            val(row, "display_name"),
            "",
        )

        return {
            **common,
            "display_name": val(row, "display_name"),
            "category": val(row, "category"),
            "ra_deg": base_ra,
            "dec_deg": base_dec,
            "coord_text": val(row, "coord_text"),
            "coord_ref": val(row, "coord_ref"),
            "status": val(row, "coord_status"),
            "source": val(row, "coord_source"),
            "resolved_at": val(row, "updated_at"),
            "query_name": query_name,
            "query_ra_deg": base_ra,
            "query_dec_deg": base_dec,
            "position_source": "targets.base_coords" if base_ra is not None and base_dec is not None else "",
        }

    if mode == "sesame":
        return {
            **common,
            "query_name": val(row, "canonical_name") or val(row, "display_name"),
            "resolver_name": "sesame",
            "sesame_oid": val(row, "coord_ref"),
            "sesame_oname": val(row, "display_name"),
            "sesame_otype": val(row, "object_type"),
            "ra_deg": val(row, "ra_deg"),
            "dec_deg": val(row, "dec_deg"),
            "coord_text": val(row, "coord_text"),
            "coord_ref": val(row, "coord_ref"),
            "status": val(row, "coord_status"),
            "source": val(row, "coord_source"),
            "resolved_at": val(row, "updated_at"),
        }

    if mode == "wikidata_name":
        return {
            **common,
            "wikidata_id": val(row, "wikidata_id"),
            "label_de": val(row, "label_de"),
            "label_en": val(row, "label_en"),
            "aliases_de": val(row, "aliases_de"),
            "aliases_en": val(row, "aliases_en"),
            "wiki_de_title": val(row, "wiki_de_title"),
            "wiki_en_title": val(row, "wiki_en_title"),
            "resolved_name": val(row, "final_name") or val(row, "display_name") or "",
            "status": val(row, "name_status"),
            "source": val(row, "name_source"),
            "resolved_at": val(row, "name_resolved_at"),
        }

    if mode == "wikidata_meta":
        return {
            **common,
            "wikidata_id": val(row, "wikidata_id"),
            "object_type": val(row, "object_type"),
            "object_type_label_de": val(row, "object_type_label_de"),
            "object_type_label_en": val(row, "object_type_label_en"),
            "mag_value": val(row, "mag_value"),
            "mag_band": val(row, "mag_band"),
            "distance_value": val(row, "distance_value"),
            "distance_unit": val(row, "distance_unit"),
            "distance_unit_label_de": val(row, "distance_unit_label_de"),
            "distance_unit_label_en": val(row, "distance_unit_label_en"),
            "status": val(row, "meta_status"),
            "source": val(row, "meta_source"),
            "resolved_at": val(row, "meta_resolved_at"),
        }

    if mode == "simbad":
        return {
            **common,
            "simbad_main_id": val(row, "simbad_main_id"),
            "simbad_otype": val(row, "simbad_otype"),
            "simbad_ra_deg": val(row, "simbad_ra_deg"),
            "simbad_dec_deg": val(row, "simbad_dec_deg"),
            "status": val(row, "simbad_status"),
            "source": val(row, "simbad_source"),
            "resolved_at": val(row, "simbad_resolved_at"),
        }

    if mode == "ned":
        return {
            **common,
            "ned_objtype": val(row, "ned_objtype"),
            "ned_ra_deg": val(row, "ned_ra_deg"),
            "ned_dec_deg": val(row, "ned_dec_deg"),
            "status": val(row, "ned_status"),
            "source": val(row, "ned_source"),
            "resolved_at": val(row, "ned_resolved_at"),
        }

    if mode == "vizier":
        return {
            **common,
            "query_name": val(row, "final_name") or val(row, "display_name") or val(row, "canonical_name"),
            "preferred_name": val(row, "final_name") or val(row, "display_name"),
            "aliases": val(row, "aliases_en") or val(row, "aliases_de"),
            "object_type": val(row, "final_objtype") or val(row, "object_type"),
            "object_type_label": val(row, "object_type_label_en") or val(row, "object_type_label_de"),
            "ra_deg": val(row, "final_ra_deg") or val(row, "ra_deg"),
            "dec_deg": val(row, "final_dec_deg") or val(row, "dec_deg"),
            "magnitude_value": val(row, "mag_value"),
            "magnitude_band": val(row, "mag_band"),
            "distance_value": val(row, "distance_value"),
            "distance_unit": val(row, "distance_unit"),
            "status": "pending",
            "source": "vizier",
            "resolved_at": None,
        }

    if mode == "ssodnet":
        category_l = (val(row, "category", "") or "").strip().lower()
        return {
            **common,
            "query_name": val(row, "final_name") or val(row, "display_name") or val(row, "canonical_name"),
            "display_name": val(row, "final_name") or val(row, "display_name"),
            "object_type": "solar_system" if category_l in ("sun", "moon", "planet", "solar_system") else "",
            "object_class": category_l,
            "status": "pending",
            "source": "ssodnet",
            "resolved_at": None,
        }

    if mode == "constellation":
        return {
            **common,
            "query_name": val(row, "canonical_name") or val(row, "display_name") or "",
            "query_ra_deg": val(row, "ra_deg"),
            "query_dec_deg": val(row, "dec_deg"),
            "position_source": "targets.base_coords" if val(row, "ra_deg") is not None and val(row, "dec_deg") is not None else "",
        }

    if mode == "nasa":
        return {
            **common,
            "nasa_title": val(row, "nasa_title"),
            "nasa_page_url": val(row, "nasa_page_url"),
            "nasa_image_url": val(row, "nasa_image_url"),
            "nasa_thumb_url": val(row, "nasa_thumb_url"),
            "status": val(row, "nasa_status"),
            "source": val(row, "nasa_source"),
            "resolved_at": val(row, "nasa_resolved_at"),
        }


    if mode == "legacy":
        return {
            **common,
            "query_name": val(row, "final_name") or val(row, "display_name") or val(row, "canonical_name"),
            "position_source": "targets.final_coords" if val(row, "final_ra_deg") is not None and val(row, "final_dec_deg") is not None else "",
            "ra_deg": val(row, "final_ra_deg"),
            "dec_deg": val(row, "final_dec_deg"),
            "status": "pending",
            "error_message": None,
        }

    if mode == "skyview":
        return {
            **common,
        }

    if mode == "irsa":
        return {
            **common,
        }

    return None


def sync_mode(db_path: str, mode: str):
    if mode not in MODES:
        raise SystemExit(
            "usage: sync_target_resolver_tables.py /runtime/pipeline.db "
            "<base|wikidata_name|wikidata_meta|simbad|ned|constellation|nasa|legacy|skyview|irsa|sesame|vizier|ssodnet>"
        )

    table = MODES[mode]
    conn = open_db(db_path)
    cur = conn.cursor()

    if not table_exists(cur, "targets"):
        raise SystemExit("targets table missing")

    if not table_exists(cur, table):
        raise SystemExit(f"{table} table missing")

    rows = cur.execute("SELECT * FROM targets ORDER BY id").fetchall()

    for row in rows:
        data = build_mode_payload(mode, row)
        if data is None:
            continue
        upsert(cur, table, "target_id", row["id"], data)

    conn.commit()
    conn.close()
    print(f"OK mode={mode}")
