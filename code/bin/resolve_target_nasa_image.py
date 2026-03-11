#!/usr/bin/env python3
import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("NASA_TIMEOUT", "30"))
USER_AGENT = os.environ.get("NASA_UA", "AstroManager/1.0")
SEARCH_URL = "https://images-api.nasa.gov/search"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def http_json(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def select_targets(conn, only_pending: bool, limit: int):
    if only_pending:
        sql = """
        select id, canonical_name, final_name, label_en, display_name
        from targets
        where coalesce(nasa_status,'pending') in ('pending','error')
        order by id
        limit ?
        """
    else:
        sql = """
        select id, canonical_name, final_name, label_en, display_name
        from targets
        order by id
        limit ?
        """
    return conn.execute(sql, (limit,)).fetchall()

def candidate_queries(row):
    vals = []
    for key in ("final_name", "label_en", "canonical_name", "display_name"):
        v = (row[key] or "").strip()
        if v and v not in vals:
            vals.append(v)
    return vals

def title_gate_terms(row):
    c = (row["canonical_name"] or "").strip().lower()
    if c == "m 31":
        return ["andromeda galaxy", "m31", "m 31", "messier 31"]
    if c == "ngc 1499":
        return ["california nebula", "ngc 1499"]
    return []

def title_passes_gate(item, gate_terms):
    if not gate_terms:
        return True
    data = item.get("data", [])
    if not data:
        return False
    d0 = data[0] or {}
    title = (d0.get("title", "") or "").lower()
    return any(term in title for term in gate_terms)

def score_item(item, query_terms):
    data = item.get("data", [])
    if not data:
        return -10_000
    d0 = data[0] or {}
    title = (d0.get("title", "") or "").lower()
    desc = (d0.get("description", "") or "").lower()

    score = 0

    exact_title_terms = [
        "andromeda galaxy",
        "m31",
        "m 31",
        "messier 31",
        "california nebula",
        "ngc 1499",
    ]
    for term in exact_title_terms:
        if title == term:
            score += 500
        elif term in title:
            score += 260

    for term in query_terms:
        t = (term or "").strip().lower()
        if not t:
            continue
        if title == t:
            score += 220
        elif t in title:
            score += 120
        if t in desc:
            score += 35

    preferred_terms = [
        "andromeda galaxy", "andromeda", "m31", "m 31", "messier 31",
        "california nebula", "ngc 1499", "california"
    ]
    for term in preferred_terms:
        if term in title:
            score += 120
        elif term in desc:
            score += 20

    bad_terms = [
        "collision", "milky way", "destined", "head-on", "artist",
        "concept", "simulation", "illustration"
    ]
    for term in bad_terms:
        if term in title:
            score -= 250
        elif term in desc:
            score -= 80

    return score

def best_item(items, query_terms, gate_terms):
    ranked = []

    for item in items:
        if not title_passes_gate(item, gate_terms):
            continue
        data = item.get("data", [])
        links = item.get("links", [])
        if not data:
            continue
        d0 = data[0] or {}
        media_type = (d0.get("media_type") or "").lower()
        if media_type != "image":
            continue

        nasa_id = d0.get("nasa_id", "") or ""
        thumb = ""
        image_url = ""
        best_alt = ""

        for link in links:
            link = link or {}
            href = link.get("href", "") or ""
            rel = (link.get("rel", "") or "").lower()
            if not href:
                continue
            if rel == "preview" and not thumb:
                thumb = href
            if rel == "canonical" and not image_url:
                image_url = href
            if rel == "alternate" and not best_alt:
                best_alt = href

        if not image_url:
            image_url = best_alt or thumb

        if nasa_id and image_url:
            ranked.append((
                score_item(item, query_terms),
                {
                    "title": d0.get("title", "") or "",
                    "nasa_id": nasa_id,
                    "thumb_url": thumb or image_url,
                    "image_url": image_url,
                    "page_url": f"https://images.nasa.gov/details-{nasa_id}",
                    "asset_manifest_url": item.get("href", "") or "",
                }
            ))

    if not ranked:
        return None

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1]

def update_success(conn, target_id: int, row: dict):
    conn.execute(
        """
        update targets
           set nasa_image_url=?,
               nasa_thumb_url=?,
               nasa_page_url=?,
               nasa_asset_manifest_url=?,
               nasa_title=?,
               nasa_nasa_id=?,
               nasa_status='resolved',
               nasa_source='nasa-image-library',
               nasa_resolved_at=datetime('now'),
               updated_at=datetime('now')
         where id=?
        """,
        (
            row["image_url"],
            row["thumb_url"],
            row["page_url"],
            row["asset_manifest_url"],
            row["title"],
            row["nasa_id"],
            target_id,
        ),
    )
    conn.commit()

def update_error(conn, target_id: int):
    conn.execute(
        """
        update targets
           set nasa_status='error',
               nasa_source='nasa-image-library',
               nasa_resolved_at=datetime('now'),
               updated_at=datetime('now')
         where id=?
        """,
        (target_id,),
    )
    conn.commit()

def resolve_one(conn, row):
    for q in candidate_queries(row):
        params = {
            "q": q,
            "media_type": "image",
            "page": "1",
        }
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
        data = http_json(url)
        items = (((data.get("collection") or {}).get("items")) or [])
        hit = best_item(items, candidate_queries(row), title_gate_terms(row))
        if hit:
            update_success(conn, row["id"], hit)
            return
    update_error(conn, row["id"])

def main():
    only_pending = "--all" not in sys.argv
    limit = 1000
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[i + 1]))

    conn = db()
    try:
        rows = select_targets(conn, only_pending, limit)
        print(f"targets_to_nasa_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            try:
                resolve_one(conn, row)
            except Exception:
                update_error(conn, row["id"])
            time.sleep(0.25)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
