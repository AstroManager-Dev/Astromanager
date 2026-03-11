#!/usr/bin/env python3
import json
import os
import sqlite3
import sys
import time
import urllib.request

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("WIKIDATA_TIMEOUT", "20"))
USER_AGENT = os.environ.get("WIKIDATA_UA", "AstroManager/1.0")
GET_URL = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&languages=de|en&props=labels&ids="

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def norm(s: str) -> str:
    return " ".join((s or "").strip().split())

def http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def fetch_labels(qid: str):
    if not qid:
        return "", ""
    data = http_json(GET_URL + qid)
    ent = data.get("entities", {}).get(qid, {})
    labels = ent.get("labels", {})
    de = norm(labels.get("de", {}).get("value", ""))
    en = norm(labels.get("en", {}).get("value", ""))
    return de, en

def select_targets(conn):
    return conn.execute("""
        select id, canonical_name, object_type, distance_unit
        from targets
        where coalesce(meta_status,'')='resolved'
          and (coalesce(object_type,'')<>'' or coalesce(distance_unit,'')<>'')
        order by id
    """).fetchall()

def main():
    conn = db()
    try:
        rows = select_targets(conn)
        print(f"targets_to_meta_label_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            obj_de, obj_en = fetch_labels(row["object_type"] or "")
            du_de, du_en = fetch_labels(row["distance_unit"] or "")
            conn.execute("""
                update targets
                   set object_type_label_de=?,
                       object_type_label_en=?,
                       distance_unit_label_de=?,
                       distance_unit_label_en=?,
                       updated_at=datetime('now')
                 where id=?
            """, (obj_de, obj_en, du_de, du_en, row["id"]))
            conn.commit()
            time.sleep(0.25)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
