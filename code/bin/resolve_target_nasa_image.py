#!/usr/bin/env python3
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("NASA_TIMEOUT", "30"))
USER_AGENT = os.environ.get("NASA_UA", "AstroManager/1.0")
SEARCH_URL = "https://images-api.nasa.gov/search"
DEFAULT_LIMIT = 1000
MIN_ACCEPT_SCORE = 260

REJECT_TITLE_TERMS = {
    "artist concept": 450,
    "artist's concept": 450,
    "illustration": 420,
    "simulation": 420,
    "concept": 220,
    "poster": 180,
    "logo": 160,
    "patch": 180,
    "crew": 180,
    "launch": 180,
    "space shuttle": 180,
    "astronaut": 180,
    "spacewalk": 160,
    "rocket": 160,
}
REJECT_DESC_TERMS = {
    "artist concept": 180,
    "artist's concept": 180,
    "illustration": 160,
    "simulation": 160,
    "concept": 90,
    "poster": 80,
    "logo": 60,
    "patch": 80,
    "crew": 80,
    "launch": 80,
    "space shuttle": 80,
    "astronaut": 80,
    "spacewalk": 70,
    "rocket": 60,
}
JWST_TERMS = ("james webb", "jwst", "webb")
HUBBLE_TERMS = ("hubble", "hst")
ALIAS_SPLIT_RE = re.compile(r"[\n,;|/]+")
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class QueryPlan:
    query: str
    aliases: tuple[str, ...]


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
    where = "where coalesce(nasa_status,'pending') in ('pending','error')" if only_pending else ""
    sql = f"""
    select
        id,
        canonical_name,
        final_name,
        label_de,
        label_en,
        display_name,
        aliases_de,
        aliases_en,
        final_objtype,
        object_type_label_de,
        object_type_label_en
    from targets
    {where}
    order by id
    limit ?
    """
    return conn.execute(sql, (limit,)).fetchall()


def normalize_text(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9+]+", " ", value)
    return SPACE_RE.sub(" ", value).strip()


def split_aliases(value: str) -> list[str]:
    out: list[str] = []
    for part in ALIAS_SPLIT_RE.split(value or ""):
        v = part.strip()
        if v:
            out.append(v)
    return out


def dedupe_keep_order(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        norm = normalize_text(value)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(value.strip())
    return out


def expand_catalog_aliases(value: str) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []

    out = [text]
    upper = text.upper().strip()
    m = re.fullmatch(r"M\s*([0-9]+)", upper)
    if m:
        n = m.group(1)
        out.extend([f"M {n}", f"M{n}", f"Messier {n}"])
    m = re.fullmatch(r"NGC\s*([0-9]+)", upper)
    if m:
        n = m.group(1)
        out.extend([f"NGC {n}", f"NGC{n}", f"New General Catalogue {n}"])
    m = re.fullmatch(r"IC\s*([0-9]+)", upper)
    if m:
        n = m.group(1)
        out.extend([f"IC {n}", f"IC{n}", f"Index Catalogue {n}"])
    return dedupe_keep_order(out)


def object_type_terms(row) -> list[str]:
    values = [row["final_objtype"], row["object_type_label_de"], row["object_type_label_en"]]
    terms: list[str] = []
    for value in values:
        norm = normalize_text(value)
        if not norm:
            continue
        if "galax" in norm:
            terms.extend(["galaxy", "galaxies"])
        if "nebel" in norm or "nebula" in norm:
            terms.extend(["nebula", "nebulae"])
        if "mond" in norm or norm == "moon":
            terms.append("moon")
        if "sonne" in norm or norm == "sun":
            terms.append("sun")
        if "sternhaufen" in norm or "cluster" in norm:
            terms.extend(["cluster", "star cluster"])
    return dedupe_keep_order(terms)


def candidate_queries(row) -> list[QueryPlan]:
    aliases: list[str] = []
    for key in (
        "final_name",
        "label_de",
        "label_en",
        "canonical_name",
        "display_name",
    ):
        aliases.extend(expand_catalog_aliases(row[key]))
    aliases.extend(split_aliases(row["aliases_de"]))
    aliases.extend(split_aliases(row["aliases_en"]))
    aliases = dedupe_keep_order(aliases)

    queries: list[QueryPlan] = []
    seen_queries: set[str] = set()
    for value in aliases:
        norm = normalize_text(value)
        if not norm or norm in seen_queries:
            continue
        seen_queries.add(norm)
        queries.append(QueryPlan(query=value, aliases=tuple(aliases)))
    return queries


def blob_text(d0: dict) -> str:
    parts = [
        d0.get("title", "") or "",
        d0.get("description", "") or "",
        d0.get("secondary_creator", "") or "",
        d0.get("center", "") or "",
        d0.get("location", "") or "",
    ]
    keywords = d0.get("keywords") or []
    if isinstance(keywords, list):
        parts.extend(str(x) for x in keywords if x)
    else:
        parts.append(str(keywords))
    return normalize_text(" ".join(parts))


def alias_variants(alias: str) -> list[str]:
    out = [alias]
    out.extend(expand_catalog_aliases(alias))
    return dedupe_keep_order(out)


def exact_alias_score(text_blob: str, title: str, aliases: Iterable[str]) -> int:
    score = 0
    norm_title = normalize_text(title)
    for alias in aliases:
        for variant in alias_variants(alias):
            norm = normalize_text(variant)
            if not norm:
                continue
            if norm_title == norm:
                score = max(score, 520)
            elif f" {norm} " in f" {norm_title} ":
                score = max(score, 360)
            elif f" {norm} " in f" {text_blob} ":
                score = max(score, 220)
    return score


def source_preference_score(text_blob: str) -> tuple[int, str]:
    for term in JWST_TERMS:
        if f" {normalize_text(term)} " in f" {text_blob} ":
            return 240, "jwst"
    for term in HUBBLE_TERMS:
        if f" {normalize_text(term)} " in f" {text_blob} ":
            return 140, "hubble"
    return 0, "generic"


def object_type_score(text_blob: str, row) -> int:
    terms = object_type_terms(row)
    if not terms:
        return 0
    for term in terms:
        norm = normalize_text(term)
        if f" {norm} " in f" {text_blob} ":
            return 45
    return 0


def reject_penalty(title: str, desc: str) -> int:
    title_norm = normalize_text(title)
    desc_norm = normalize_text(desc)
    penalty = 0
    for term, value in REJECT_TITLE_TERMS.items():
        norm = normalize_text(term)
        if f" {norm} " in f" {title_norm} ":
            penalty += value
    for term, value in REJECT_DESC_TERMS.items():
        norm = normalize_text(term)
        if f" {norm} " in f" {desc_norm} ":
            penalty += value
    return penalty


def score_item(item, query_plan: QueryPlan, row) -> tuple[int, str]:
    data = item.get("data", [])
    if not data:
        return -10_000, "missing-data"
    d0 = data[0] or {}
    title = d0.get("title", "") or ""
    desc = d0.get("description", "") or ""
    text_blob = blob_text(d0)

    alias_score = exact_alias_score(text_blob, title, query_plan.aliases)
    query_score = exact_alias_score(text_blob, title, [query_plan.query])
    source_score, source_tag = source_preference_score(text_blob)
    type_score = object_type_score(text_blob, row)
    penalty = reject_penalty(title, desc)

    score = alias_score + query_score + source_score + type_score - penalty

    if alias_score == 0 and query_score == 0:
        score -= 300
    if penalty >= 400:
        score -= 200

    return score, source_tag


def build_ranked_item(item, query_plan: QueryPlan, row):
    data = item.get("data", [])
    links = item.get("links", [])
    if not data:
        return None
    d0 = data[0] or {}
    media_type = normalize_text(d0.get("media_type") or "")
    if media_type != "image":
        return None

    nasa_id = d0.get("nasa_id", "") or ""
    thumb = ""
    image_url = ""
    best_alt = ""

    for link in links:
        link = link or {}
        href = link.get("href", "") or ""
        rel = normalize_text(link.get("rel", "") or "")
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
    if not nasa_id or not image_url:
        return None

    score, source_tag = score_item(item, query_plan, row)
    return (
        score,
        {
            "title": d0.get("title", "") or "",
            "nasa_id": nasa_id,
            "thumb_url": thumb or image_url,
            "image_url": image_url,
            "page_url": f"https://images.nasa.gov/details-{nasa_id}",
            "asset_manifest_url": item.get("href", "") or "",
            "source_tag": source_tag,
            "query_name": query_plan.query,
            "match_name": d0.get("title", "") or "",
            "match_method": f"name+source:{source_tag}",
            "match_confidence": round(max(0, min(1, score / 700)), 4),
            "raw_payload": json.dumps(d0, ensure_ascii=False),
        },
    )


def best_item(items, query_plan: QueryPlan, row):
    ranked = []
    for item in items:
        built = build_ranked_item(item, query_plan, row)
        if built:
            ranked.append(built)
    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_row = ranked[0]
    best_row["score"] = best_score
    if best_score < MIN_ACCEPT_SCORE:
        return None
    return best_row


def update_success(conn, target_id: int, row: dict, *, dry_run: bool):
    source_value = "nasa-image-library"
    if row.get("source_tag") in {"jwst", "hubble"}:
        source_value = f"nasa-image-library:{row['source_tag']}"

    if dry_run:
        print(
            f"dry-run success target_id={target_id} source={source_value} "
            f"score={row.get('score')} query={row.get('query_name')} title={row.get('title')}"
        )
        return

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
               nasa_source=?,
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
            source_value,
            target_id,
        ),
    )
    conn.commit()


def update_error(conn, target_id: int, *, dry_run: bool, message: str = ""):
    if dry_run:
        print(f"dry-run error target_id={target_id} message={message}")
        return

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


def resolve_one(conn, row, *, dry_run: bool):
    for query_plan in candidate_queries(row):
        params = {
            "q": query_plan.query,
            "media_type": "image",
            "page": "1",
        }
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
        data = http_json(url)
        items = (((data.get("collection") or {}).get("items")) or [])
        hit = best_item(items, query_plan, row)
        if hit:
            update_success(conn, row["id"], hit, dry_run=dry_run)
            return
    update_error(conn, row["id"], dry_run=dry_run, message="no-acceptable-match")


def parse_args(argv: list[str]):
    only_pending = "--all" not in argv
    dry_run = "--dry-run" in argv
    limit = DEFAULT_LIMIT
    if "--limit" in argv:
        i = argv.index("--limit")
        if i + 1 < len(argv):
            limit = max(1, int(argv[i + 1]))
    return only_pending, dry_run, limit


def main():
    only_pending, dry_run, limit = parse_args(sys.argv)
    conn = db()
    try:
        rows = select_targets(conn, only_pending, limit)
        print(f"targets_to_nasa_resolve={len(rows)} dry_run={str(dry_run).lower()}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            try:
                resolve_one(conn, row, dry_run=dry_run)
            except Exception as exc:
                update_error(conn, row["id"], dry_run=dry_run, message=str(exc))
            time.sleep(0.25)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
