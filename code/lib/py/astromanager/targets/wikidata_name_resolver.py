#!/usr/bin/env python3
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request

from astromanager.targets.distance_normalizer import normalize_distance_to_ly
from astromanager.targets.wikidata_match_utils import (
    angular_sep_deg,
    best_catalog_fallback_name,
    claim_coord,
    claim_entity_id,
    claim_quantity,
    coord_score,
    entity_anchor_score,
    hit_name_score,
    labels_aliases,
    norm,
    reject_entity_mismatch,
    row_search_terms,
    sitelink_title,
)

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("WIKIDATA_TIMEOUT", "20"))
USER_AGENT = os.environ.get("WIKIDATA_UA", "AstroManager/1.0")
SEARCH_URL = "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=en&type=item&limit=10&search="
GET_URL = "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&languages=de|en&sitefilter=dewiki|enwiki&props=labels|aliases|sitelinks|claims&ids="
MAX_SEP_DEG = float(os.environ.get("WIKIDATA_MAX_SEP_DEG", "2.0"))


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def http_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def select_targets(conn, only_pending: bool, limit: int):
    if only_pending:
        sql = """
        select id, canonical_name, display_name, final_name, simbad_main_id, ned_preferred_name,
               wikidata_id, category, coord_status, name_status, meta_status, ra_deg, dec_deg
        from targets
        where coord_status='resolved'
          and (
                coalesce(name_status,'pending') in ('pending','error')
             or coalesce(meta_status,'pending') in ('pending','error')
             or coalesce(wikidata_id,'')=''
          )
          and lower(coalesce(category,'')) not in ('sun','moon')
        order by id
        limit ?
        """
    else:
        sql = """
        select id, canonical_name, display_name, final_name, simbad_main_id, ned_preferred_name,
               wikidata_id, category, coord_status, name_status, meta_status, ra_deg, dec_deg
        from targets
        where coord_status='resolved'
          and lower(coalesce(category,'')) not in ('sun','moon')
        order by id
        limit ?
        """
    return conn.execute(sql, (limit,)).fetchall()


def update_success(
    conn,
    target_id: int,
    qid: str,
    label_de: str,
    label_en: str,
    aliases_de: list[str],
    aliases_en: list[str],
    wiki_de_title: str,
    wiki_en_title: str,
    object_type: str,
    mag_value,
    mag_band: str,
    distance_value,
    distance_unit: str,
    distance_ly,
    catalog_fallback_name: str,
):
    effective_label_de = label_de or (aliases_de[0] if aliases_de else "")
    effective_display = effective_label_de or label_en or (aliases_en[0] if aliases_en else "") or catalog_fallback_name
    name_status = "resolved" if effective_display else "unresolved"

    conn.execute(
        """
        update targets
           set wikidata_id=?,
               label_de=?,
               label_en=?,
               aliases_de=?,
               aliases_en=?,
               wiki_de_title=?,
               wiki_en_title=?,
               object_type=?,
               mag_value=?,
               mag_band=?,
               distance_value=?,
               distance_unit=?,
               distance_ly=?,
               distance_source=case when ? is not null then 'wikidata' else distance_source end,
               display_name=case when ?<>'' then ? else display_name end,
               name_status=?,
               name_source='wikidata',
               name_resolved_at=datetime('now'),
               meta_status='resolved',
               meta_source='wikidata',
               meta_resolved_at=datetime('now'),
               updated_at=datetime('now')
         where id=?
        """,
        (
            qid,
            effective_label_de,
            label_en,
            json.dumps(aliases_de, ensure_ascii=False),
            json.dumps(aliases_en, ensure_ascii=False),
            wiki_de_title,
            wiki_en_title,
            object_type,
            mag_value,
            mag_band,
            distance_value,
            distance_unit,
            distance_ly,
            distance_ly,
            effective_display,
            effective_display,
            name_status,
            target_id,
        ),
    )
    conn.commit()


def update_error(conn, target_id: int):
    conn.execute(
        """
        update targets
           set wikidata_id='',
               label_de='',
               label_en='',
               aliases_de='[]',
               aliases_en='[]',
               wiki_de_title='',
               wiki_en_title='',
               object_type='',
               mag_value=null,
               mag_band='',
               distance_value=null,
               distance_unit='',
               distance_ly=null,
               distance_source='',
               name_status='error',
               name_source='wikidata',
               name_resolved_at=datetime('now'),
               meta_status='error',
               meta_source='wikidata',
               meta_resolved_at=datetime('now'),
               updated_at=datetime('now')
         where id=?
        """,
        (target_id,),
    )
    conn.commit()


def collect_candidates(row):
    aggregated = {}

    for term in row_search_terms(row):
        search_data = http_json(SEARCH_URL + urllib.parse.quote(term))
        for hit in search_data.get("search", []):
            qid = norm(hit.get("id", ""))
            if not qid:
                continue

            entry = aggregated.setdefault(
                qid,
                {
                    "hit": hit,
                    "terms": [],
                },
            )
            if term not in entry["terms"]:
                entry["terms"].append(term)

    return aggregated


def resolve_one(conn, row):
    target_ra = row["ra_deg"]
    target_dec = row["dec_deg"]

    aggregated = collect_candidates(row)
    if not aggregated:
        update_error(conn, row["id"])
        return

    checked = []

    for qid, item in aggregated.items():
        entity_data = http_json(GET_URL + urllib.parse.quote(qid))
        entity = entity_data.get("entities", {}).get(qid, {})
        if not entity:
            continue

        rejected, reject_reason = reject_entity_mismatch(row, entity)
        if rejected:
            continue

        cand_ra, cand_dec = claim_coord(entity)
        sep = None
        if target_ra is not None and target_dec is not None and cand_ra is not None and cand_dec is not None:
            sep = angular_sep_deg(target_ra, target_dec, cand_ra, cand_dec)

        name_score = max([hit_name_score(term, item["hit"], entity) for term in item["terms"]] or [0])
        anchor_score = entity_anchor_score(row, entity)
        total_score = anchor_score + name_score + coord_score(sep, MAX_SEP_DEG)

        checked.append(
            {
                "qid": qid,
                "entity": entity,
                "sep": sep,
                "name_score": name_score,
                "anchor_score": anchor_score,
                "total_score": total_score,
                "reject_reason": reject_reason,
            }
        )

    if not checked:
        update_error(conn, row["id"])
        return

    checked.sort(
        key=lambda item: (
            -item["total_score"],
            -item["anchor_score"],
            -item["name_score"],
            item["sep"] if item["sep"] is not None else 999999.0,
        )
    )

    chosen = checked[0]

    if (
        chosen["anchor_score"] < 80
        and chosen["name_score"] < 100
        and (chosen["sep"] is None or chosen["sep"] > MAX_SEP_DEG)
    ):
        update_error(conn, row["id"])
        return

    entity = chosen["entity"]
    qid = chosen["qid"]

    label_de, aliases_de = labels_aliases(entity, "de")
    label_en, aliases_en = labels_aliases(entity, "en")
    wiki_de_title = sitelink_title(entity, "dewiki")
    wiki_en_title = sitelink_title(entity, "enwiki")
    object_type = claim_entity_id(entity, "P31")
    mag_value, _mag_unit = claim_quantity(entity, "P1215")
    mag_band = "P1215"
    distance_value, distance_unit = claim_quantity(entity, "P2583")

    distance_ly, _distance_norm_unit = normalize_distance_to_ly(
        distance_value,
        distance_unit,
        "",
        "",
    )

    catalog_fallback_name = best_catalog_fallback_name(entity)

    update_success(
        conn,
        row["id"],
        qid,
        label_de,
        label_en,
        aliases_de,
        aliases_en,
        wiki_de_title,
        wiki_en_title,
        object_type,
        mag_value,
        mag_band if mag_value is not None else "",
        distance_value,
        distance_unit,
        distance_ly,
        catalog_fallback_name,
    )


def run(only_pending: bool = True, limit: int = 1000) -> int:
    conn = db()
    try:
        rows = select_targets(conn, only_pending, limit)
        print(f"targets_to_name_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            try:
                resolve_one(conn, row)
            except Exception:
                update_error(conn, row["id"])
            time.sleep(0.25)
    finally:
        conn.close()

    return 0
