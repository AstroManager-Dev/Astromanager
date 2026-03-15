#!/usr/bin/env python3
import json
import os
import sqlite3
import time
import urllib.request

from astromanager.targets.distance_normalizer import normalize_distance_to_ly

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("WIKIDATA_TIMEOUT", "20"))
USER_AGENT = os.environ.get("WIKIDATA_UA", "AstroManager/1.0")
GET_URL = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&languages=de|en&props=labels&ids="


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def norm(value: str) -> str:
    return " ".join((value or "").strip().split())


def http_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def fetch_labels(qid: str):
    qid = norm(qid)
    if not qid:
        return "", ""

    data = http_json(GET_URL + qid)
    entity = data.get("entities", {}).get(qid, {})
    labels = entity.get("labels", {})

    label_de = norm(labels.get("de", {}).get("value", ""))
    label_en = norm(labels.get("en", {}).get("value", ""))

    return label_de, label_en


def select_targets(conn, only_missing: bool, limit: int):
    if only_missing:
        sql = """
        SELECT id, canonical_name, object_type, distance_unit, distance_value,
               object_type_label_de, object_type_label_en,
               distance_unit_label_de, distance_unit_label_en
          FROM targets
         WHERE coalesce(meta_status,'')='resolved'
           AND (
                (
                  coalesce(object_type,'') <> ''
                  AND (
                       coalesce(object_type_label_de,'') = ''
                    OR coalesce(object_type_label_en,'') = ''
                  )
                )
             OR (
                  coalesce(distance_unit,'') <> ''
                  AND (
                       coalesce(distance_unit_label_de,'') = ''
                    OR coalesce(distance_unit_label_en,'') = ''
                  )
                )
           )
         ORDER BY id
         LIMIT ?
        """
    else:
        sql = """
        SELECT id, canonical_name, object_type, distance_unit, distance_value,
               object_type_label_de, object_type_label_en,
               distance_unit_label_de, distance_unit_label_en
          FROM targets
         WHERE coalesce(meta_status,'')='resolved'
           AND (
                coalesce(object_type,'') <> ''
             OR coalesce(distance_unit,'') <> ''
           )
         ORDER BY id
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def update_target(conn, row_id: int, obj_de: str, obj_en: str, dist_de: str, dist_en: str, distance_ly):
    conn.execute(
        """
        UPDATE targets
           SET object_type_label_de=?,
               object_type_label_en=?,
               distance_unit_label_de=?,
               distance_unit_label_en=?,
               distance_ly=COALESCE(?, distance_ly),
               distance_source=case when ? is not null then 'wikidata' else distance_source end,
               updated_at=datetime('now')
         WHERE id=?
        """,
        (obj_de, obj_en, dist_de, dist_en, distance_ly, distance_ly, row_id),
    )


def run(only_missing: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_missing=only_missing, limit=limit)
        print(f"targets_to_meta_label_resolve={len(rows)}")

        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")

            obj_de, obj_en = fetch_labels(row["object_type"] or "")
            dist_de, dist_en = fetch_labels(row["distance_unit"] or "")

            distance_ly, _distance_norm_unit = normalize_distance_to_ly(
                row["distance_value"],
                row["distance_unit"] or "",
                dist_de,
                dist_en,
            )

            update_target(conn, row["id"], obj_de, obj_en, dist_de, dist_en, distance_ly)
            conn.commit()
            time.sleep(0.25)
    finally:
        conn.close()

    return 0
