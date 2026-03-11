#!/usr/bin/env python3
import math
import re


def norm(s: str) -> str:
    return " ".join((s or "").strip().split())


def compact_name(s: str) -> str:
    s = norm(s).lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def canonicalize_catalog_name(s: str) -> str:
    raw = compact_name(s)
    m = re.match(r"^(ngc|ic|m|messier)0*([0-9]+[a-z]?)$", raw)
    if m:
        prefix = m.group(1)
        num = m.group(2)
        if prefix == "messier":
            prefix = "m"
        return f"{prefix}{num}"
    return raw


def same_name(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if compact_name(a) == compact_name(b):
        return True
    if canonicalize_catalog_name(a) == canonicalize_catalog_name(b):
        return True
    return False


def angular_sep_deg(ra1, dec1, ra2, dec2):
    r1 = math.radians(float(ra1))
    d1 = math.radians(float(dec1))
    r2 = math.radians(float(ra2))
    d2 = math.radians(float(dec2))
    cosv = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    cosv = max(-1.0, min(1.0, cosv))
    return math.degrees(math.acos(cosv))


def coord_score(sep, max_sep_deg: float) -> int:
    if sep is None:
        return 0
    if sep <= 0.01:
        return 60
    if sep <= 0.05:
        return 50
    if sep <= 0.2:
        return 40
    if sep <= max_sep_deg:
        return 20
    return -60


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


def claim_all_strings(entity: dict, prop: str) -> list[str]:
    claims = entity.get("claims", {})
    rows = claims.get(prop, [])
    out = []
    for row in rows:
        value = row.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, str):
            value = norm(value)
            if value and value not in out:
                out.append(value)
    return out


def claim_entity_id(entity: dict, prop: str) -> str:
    value = claim_first(entity, prop)
    if isinstance(value, dict):
        return norm(str(value.get("id", "")))
    return ""


def claim_string(entity: dict, prop: str) -> str:
    value = claim_first(entity, prop)
    if isinstance(value, str):
        return norm(value)
    if isinstance(value, dict):
        if "text" in value:
            return norm(value.get("text", ""))
        if "id" in value:
            return norm(value.get("id", ""))
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
    return float(ra), float(dec)


def entity_candidate_names(entity: dict) -> list[str]:
    names = []

    for lang in ("de", "en"):
        label, aliases = labels_aliases(entity, lang)
        if label and label not in names:
            names.append(label)
        for alias in aliases:
            if alias and alias not in names:
                names.append(alias)

    for key in ("dewiki", "enwiki"):
        title = sitelink_title(entity, key)
        if title and title not in names:
            names.append(title)

    for value in claim_all_strings(entity, "P528"):
        if value not in names:
            names.append(value)

    p373 = claim_string(entity, "P373")
    if p373 and p373 not in names:
        names.append(p373)

    return names


def row_search_terms(row) -> list[str]:
    terms = []
    for key in ("simbad_main_id", "final_name", "ned_preferred_name", "canonical_name"):
        value = norm(row[key] or "")
        if value and value not in terms:
            terms.append(value)
    return terms


def hit_name_score(search_name: str, hit: dict, entity: dict) -> int:
    search_l = norm(search_name).lower()
    compact = compact_name(search_name)
    score = 0

    label = norm(hit.get("label", "")).lower()
    match_text = norm(hit.get("match", {}).get("text", "")).lower()
    desc = norm(hit.get("description", "")).lower()

    if label == search_l:
        score += 100
    elif compact_name(label) == compact:
        score += 90
    elif same_name(label, search_name):
        score += 85

    if match_text == search_l:
        score += 80
    elif compact_name(match_text) == compact:
        score += 70
    elif same_name(match_text, search_name):
        score += 65

    for candidate in entity_candidate_names(entity):
        if candidate.lower() == search_l:
            score += 60
            break
        if compact_name(candidate) == compact:
            score += 50
            break
        if same_name(candidate, search_name):
            score += 45
            break

    astro_words = (
        "galaxy", "nebula", "cluster", "quasar", "astronomical", "astronomy",
        "spiral", "barred", "emission", "planetary", "h ii", "region"
    )
    if any(word in desc for word in astro_words):
        score += 10

    return score


def entity_anchor_score(row, entity: dict) -> int:
    score = 0
    candidate_names = entity_candidate_names(entity)
    simbad_claim = claim_string(entity, "P3083")
    p528_values = claim_all_strings(entity, "P528")

    simbad_anchor = norm(row["simbad_main_id"] or "")
    ned_anchor = norm(row["ned_preferred_name"] or "")
    final_anchor = norm(row["final_name"] or "")
    canonical_anchor = norm(row["canonical_name"] or "")

    if simbad_anchor and simbad_claim:
        if same_name(simbad_claim, simbad_anchor):
            score += 220
        else:
            score -= 160

    weighted_anchors = [
        (final_anchor, 110),
        (ned_anchor, 95),
        (simbad_anchor, 90),
        (canonical_anchor, 60),
    ]

    for anchor, weight in weighted_anchors:
        if not anchor:
            continue

        matched = False
        for candidate in candidate_names:
            if same_name(candidate, anchor):
                score += weight
                matched = True
                break

        if not matched:
            for value in p528_values:
                if same_name(value, anchor):
                    score += weight + 40
                    matched = True
                    break

    return score


def strong_consensus_anchor(row) -> str:
    anchors = [norm(row[k] or "") for k in ("final_name", "simbad_main_id", "ned_preferred_name")]
    anchors = [a for a in anchors if a]
    if len(anchors) < 2:
        return ""

    base = canonicalize_catalog_name(anchors[0])
    if not base:
        return ""

    for other in anchors[1:]:
        if canonicalize_catalog_name(other) != base:
            return ""
    return anchors[0]


def entity_matches_anchor(entity: dict, anchor: str) -> bool:
    if not anchor:
        return False

    anchor_cat = canonicalize_catalog_name(anchor)
    is_catalog_anchor = bool(re.match(r"^(m|ngc|ic)[0-9]+[a-z]?$", anchor_cat))

    simbad_claim = claim_string(entity, "P3083")
    if simbad_claim and same_name(simbad_claim, anchor):
        return True

    for value in claim_all_strings(entity, "P528"):
        if same_name(value, anchor):
            return True

    p373 = claim_string(entity, "P373")
    if p373 and same_name(p373, anchor):
        return True

    wiki_titles = []
    for key in ("dewiki", "enwiki"):
        title = sitelink_title(entity, key)
        if title:
            wiki_titles.append(title)

    for title in wiki_titles:
        if same_name(title, anchor):
            return True

    if is_catalog_anchor:
        return False

    for name in entity_candidate_names(entity):
        if same_name(name, anchor):
            return True

    return False


def reject_entity_mismatch(row, entity: dict) -> tuple[bool, str]:
    simbad_anchor = norm(row["simbad_main_id"] or "")
    simbad_claim = claim_string(entity, "P3083")

    if simbad_anchor and simbad_claim and not same_name(simbad_anchor, simbad_claim):
        return True, "simbad_claim_mismatch"

    consensus = strong_consensus_anchor(row)
    if consensus and not entity_matches_anchor(entity, consensus):
        return True, "strong_anchor_mismatch"

    return False, ""


def best_catalog_fallback_name(entity: dict) -> str:
    for value in claim_all_strings(entity, "P528"):
        if value:
            return value

    p373 = claim_string(entity, "P373")
    if p373:
        return p373

    return ""
