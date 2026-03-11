#!/usr/bin/env python3
import json
import math
import os
import sqlite3
import time
import urllib.parse
import urllib.request

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


def norm(s: str) -> str:
    return " ".join((s or "").strip().split())


def http_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def angular_sep_deg(ra1, dec1, ra2, dec2):
    r1 = math.radians(float(ra1))
    d1 = math.radians(float(dec1))
    r2 = math.radians(float(ra2))
    d2 = math.radians(float(dec2))
    cosv = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    cosv = max(-1.0, min(1.0, cosv))
    return math.degrees(math.acos(cosv))


def hit_name_score(canonical_name: str, hit: dict, entity: dict) -> int:
    canonical_l = norm(canonical_name).lower()
    compact = canonical_l.replace(" ", "")
    score = 0

    label = norm(hit.get("label", "")).lower()
    match_text = norm(hit.get("match", {}).get("text", "")).lower()
    desc = norm(hit.get("description", "")).lower()

    if label == canonical_l:
        score += 100
    elif label.replace(" ", "") == compact:
        score += 90

    if match_text == canonical_l:
        score += 80
    elif match_text.replace(" ", "") == compact:
        score += 70

    aliases = []
    for lang in ("de", "en"):
        for row in entity.get("aliases", {}).get(lang, []):
            value = norm(row.get("value", "")).lower()
            if value:
                aliases.append(value)

    if canonical_l in aliases:
        score += 60
    elif compact in [a.replace(" ", "") for a in aliases]:
        score += 50

    astro_words = (
        "galaxy", "nebula", "cluster", "quasar", "astronomical", "astronomy",
        "spiral", "barred", "emission", "planetary", "h ii", "region"
    )
    if any(word in desc for word in astro_words):
        score += 10

    return score


def pick_best_search_hit(canonical_name: str, hits: list[dict], entities: dict[str, dict]) -> dict | None:
    if not hits:
        return None

    ranked = []
    for hit in hits:
        qid = hit.get("id", "")
        entity = entities.get(qid, {})
        ranked.append((hit_name_score(canonical_name, hit, entity), hit))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1] if ranked else None


def labels_aliases(entity: dict, lang: str):
    labels = entity.get("labels", {})
    aliases = entity.get("aliases", {})
    label = norm(labels.get(lang, {}).get("value", ""))

    alias_values = []
    for row in aliases.get(lang, []):
        value = norm(row.get("value", ""))
        if value and value not in alias_values:
            alias_values.append(value)

    return label, alias_values


def sitelink_title(entity: dict, key: str) -> str:
    return norm(entity.get("sitelinks", {}).get(key, {}).get("title", ""))


def claim_first(entity: dict, prop: str):
    claims = entity.get("claims", {})
    rows = claims.get(prop, [])
    if not rows:
        return None

    preferred = []
    normal = []

    for row in rows:
        rank = row.get("rank", "")
        value = row.get("mainsnak", {}).get("datavalue", {}).get("value")
        if value is None:
            continue
        if rank == "preferred":
            preferred.append(value)
        elif rank == "normal":
            normal.append(value)

    if preferred:
        return preferred[0]
    if normal:
        return normal[0]
    return None


def claim_entity_id(entity: dict, prop: str) -> str:
    value = claim_first(entity, prop)
    if isinstance(value, dict):
        return norm(str(value.get("id", "")))
    return ""


def claim_quantity(entity: dict, prop: str):
    value = claim_first(entity, prop)
    if not isinstance(value, dict):
        return None, ""

    amount = value.get("amount")
    unit = value.get("unit", "")
    number = None

    if amount is not None:
        try:
            number = float(str(amount).replace("+", ""))
        except Exception:
            number = None

    if unit and unit.startswith("http://www.wikidata.org/entity/"):
        unit = unit.rsplit("/", 1)[-1]

    return number, unit


def claim_coord(entity: dict):
    ra, _ = claim_quantity(entity, "P6257")
    dec, _ = claim_quantity(entity, "P6258")
    if ra is None or dec is None:
        return None, None

    try:
        return float(ra), float(dec)
    except Exception:
        return None, None


def select_targets(conn, only_pending: bool, limit: int):
    if only_pending:
        sql = """
        select id, canonical_name, display_name, category, coord_status, name_status, meta_status, ra_deg, dec_deg
        from targets
        where coord_status='resolved'
          and (
                coalesce(name_status,'pending') in ('pending','error')
             or coalesce(meta_status,'pending') in ('pending','error')
          )
          and lower(coalesce(category,'')) not in ('sun','moon')
        order by id
        limit ?
        """
    else:
        sql = """
        select id, canonical_name, display_name, category, coord_status, name_status, meta_status, ra_deg, dec_deg
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
):
    effective_label_de = label_de or (aliases_de[0] if aliases_de else "")
    effective_display = effective_label_de or label_en or (aliases_en[0] if aliases_en else "")
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
           set name_status='error',
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


def resolve_one(conn, row):
    canonical_name = norm(row["canonical_name"])
    target_ra = row["ra_deg"]
    target_dec = row["dec_deg"]

    search_data = http_json(SEARCH_URL + urllib.parse.quote(canonical_name))
    hits = search_data.get("search", [])
    if not hits:
        update_error(conn, row["id"])
        return

    checked = []
    entity_map = {}

    for hit in hits:
        qid = hit.get("id", "")
        if not qid:
            continue

        entity_data = http_json(GET_URL + urllib.parse.quote(qid))
        entity = entity_data.get("entities", {}).get(qid, {})
        if not entity:
            continue

        entity_map[qid] = entity
        cand_ra, cand_dec = claim_coord(entity)
        sep = None

        if target_ra is not None and target_dec is not None and cand_ra is not None and cand_dec is not None:
            sep = angular_sep_deg(target_ra, target_dec, cand_ra, cand_dec)

        checked.append((hit, entity, sep, hit_name_score(canonical_name, hit, entity)))

    chosen_hit = None
    chosen_entity = None

    coord_matches = [
        (hit, entity, sep, score)
        for (hit, entity, sep, score) in checked
        if sep is not None and sep <= MAX_SEP_DEG and score >= 50
    ]

    if coord_matches:
        coord_matches.sort(key=lambda item: (-item[3], item[2]))
        chosen_hit, chosen_entity, _, _ = coord_matches[0]
    else:
        fallback_hit = pick_best_search_hit(canonical_name, hits, entity_map)
        if not fallback_hit:
            update_error(conn, row["id"])
            return

        qid = fallback_hit.get("id", "")
        chosen_entity = entity_map.get(qid, {})
        chosen_hit = fallback_hit

        if not chosen_entity:
            update_error(conn, row["id"])
            return

    qid = chosen_hit.get("id", "")
    label_de, aliases_de = labels_aliases(chosen_entity, "de")
    label_en, aliases_en = labels_aliases(chosen_entity, "en")
    wiki_de_title = sitelink_title(chosen_entity, "dewiki")
    wiki_en_title = sitelink_title(chosen_entity, "enwiki")
    object_type = claim_entity_id(chosen_entity, "P31")
    mag_value, _mag_unit = claim_quantity(chosen_entity, "P1215")
    mag_band = "P1215"
    distance_value, distance_unit = claim_quantity(chosen_entity, "P2583")

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
