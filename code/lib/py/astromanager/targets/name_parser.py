#!/usr/bin/env python3
import json
import re


def parse_aliases(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return [text]


def normalize_name_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def lower_compact(value):
    return normalize_name_text(value).lower().replace(" ", "")


def normalize_catalog_name(value):
    s = normalize_name_text(value)
    if not s:
        return ""

    sl = s.lower()

    patterns = [
        (r"^new general catalogue\s*0*(\d+[a-z]?)$", lambda m: f"NGC {m.group(1).upper()}"),
        (r"^ngc\s*0*(\d+[a-z]?)$", lambda m: f"NGC {m.group(1).upper()}"),
        (r"^ic\s*0*(\d+[a-z]?)$", lambda m: f"IC {m.group(1).upper()}"),
        (r"^messier\s*0*(\d+)$", lambda m: f"M {int(m.group(1))}"),
        (r"^m\s*0*(\d+)$", lambda m: f"M {int(m.group(1))}"),
    ]

    for pattern, formatter in patterns:
        match = re.match(pattern, sl)
        if match:
            return formatter(match)

    return s


def detect_name_class(value):
    s = normalize_catalog_name(value)
    if not s:
        return "empty"

    sl = s.lower()

    if re.match(r"^m\s+\d+$", sl):
        return "messier"

    if re.match(r"^(ngc|ic)\s+\d+[a-z]?$", sl):
        return "ngc_ic"

    if re.match(r"^(ugc|pgc|sh2|sh2-|barnard|ldn|rcw|vdb|gum|mcg|isoss|2masx)\b", sl):
        return "other_catalog"

    if is_nice_common_name(s):
        return "common_name"

    if re.search(r"[a-zäöüß]", s, flags=re.IGNORECASE) and not re.search(r"\d", s):
        return "common_name"

    return "raw_name"


def class_priority(name_class):
    priorities = {
        "common_name": 500,
        "messier": 400,
        "ngc_ic": 300,
        "other_catalog": 200,
        "raw_name": 100,
        "empty": -999,
    }
    return priorities.get(name_class, 0)


def source_priority(source):
    priorities = {
        "label_de": 100,
        "alias_de": 90,
        "wiki_de_title": 80,
        "display_name": 70,
        "label_en": 60,
        "alias_en": 50,
        "wiki_en_title": 40,
        "simbad_main_id": 30,
        "ned_preferred_name": 20,
        "canonical_name": 10,
    }
    return priorities.get(source, 0)


def is_catalog_like_name(value):
    s = normalize_catalog_name(value)
    if not s:
        return False

    compact = lower_compact(s)
    prefixes = (
        "ngc", "ic", "m", "messier", "sh2-", "sh2", "sharpless",
        "barnard", "ugc", "pgc", "ldn", "rcw", "vdb", "gum", "mcg",
        "isoss", "2masx"
    )
    return compact.startswith(prefixes)


def is_plain_catalog_label(value):
    s = normalize_catalog_name(value)
    if not s:
        return False

    sl = s.lower()
    patterns = [
        r"^m\s+\d+$",
        r"^ngc\s+\d+[a-z]?$",
        r"^ic\s+\d+[a-z]?$",
        r"^isoss\s+\S+$",
        r"^mcg\s+.+$",
        r"^ugc\s+\d+$",
        r"^pgc\s+\d+$",
        r"^2masx\s+\S+$",
        r"^(dwarf elliptical galaxy|elliptical galaxy|spiral galaxy|barred spiral galaxy|irregular galaxy|lenticular galaxy|emission nebula|reflection nebula|planetary nebula|globular cluster|open cluster)\s+(m|ngc|ic)\s*\S+$",
    ]
    return any(re.match(pattern, sl) for pattern in patterns)


def is_nice_common_name(value):
    s = normalize_name_text(value)
    if not s:
        return False

    sl = s.lower()

    if is_plain_catalog_label(s):
        return False
    if is_catalog_like_name(s):
        return False

    positive_words = (
        "galaxie", "galaxy", "nebel", "nebula", "cluster", "haufen"
    )
    if any(word in sl for word in positive_words):
        return True

    special_terms = (
        "andromeda", "california", "californien", "bodes", "zigarren", "cigar"
    )
    return any(term in sl for term in special_terms)


def rank_name(value, source="", canonical_name="", simbad_main_id="", ned_preferred_name=""):
    s = normalize_catalog_name(value)
    if not s:
        return -999

    score = 0
    name_class = detect_name_class(s)
    score += class_priority(name_class)
    score += source_priority(source)

    canonical_c = lower_compact(normalize_catalog_name(canonical_name))
    simbad_c = lower_compact(normalize_catalog_name(simbad_main_id))
    ned_c = lower_compact(normalize_catalog_name(ned_preferred_name))
    current_c = lower_compact(s)

    if name_class == "common_name":
        score += 25

    if name_class == "messier":
        score += 20

    if name_class == "ngc_ic":
        score += 10

    if current_c == simbad_c:
        score += 8

    if current_c == ned_c:
        score += 4

    if current_c == canonical_c:
        score -= 5

    if re.match(r"^new general catalogue\s+", normalize_name_text(value).lower()):
        score -= 50

    if len(s) >= 4:
        score += 3

    return score


def best_alias(alias_list, canonical_name="", simbad_main_id="", ned_preferred_name=""):
    cleaned = []
    seen = set()

    for alias in alias_list:
        alias_name = normalize_catalog_name(alias)
        alias_name = normalize_name_text(alias_name)
        if not alias_name:
            continue

        alias_compact = lower_compact(alias_name)
        if alias_compact in seen:
            continue

        seen.add(alias_compact)
        cleaned.append(alias_name)

    if not cleaned:
        return ""

    cleaned.sort(
        key=lambda value: (
            -rank_name(
                value,
                source="alias",
                canonical_name=canonical_name,
                simbad_main_id=simbad_main_id,
                ned_preferred_name=ned_preferred_name,
            ),
            len(value),
            value.lower(),
        )
    )
    return cleaned[0]


def choose_final_name(row):
    canonical_name = normalize_catalog_name(row["canonical_name"] or "")
    display_name = normalize_catalog_name(row["display_name"] or "")
    label_de = normalize_catalog_name(row["label_de"] or "")
    label_en = normalize_catalog_name(row["label_en"] or "")
    wiki_de_title = normalize_catalog_name(row["wiki_de_title"] or "")
    wiki_en_title = normalize_catalog_name(row["wiki_en_title"] or "")
    ned_preferred_name = normalize_catalog_name(row["ned_preferred_name"] or "")
    simbad_main_id = normalize_catalog_name(row["simbad_main_id"] or "")

    alias_de = best_alias(
        parse_aliases(row["aliases_de"]),
        canonical_name=canonical_name,
        simbad_main_id=simbad_main_id,
        ned_preferred_name=ned_preferred_name,
    )
    alias_en = best_alias(
        parse_aliases(row["aliases_en"]),
        canonical_name=canonical_name,
        simbad_main_id=simbad_main_id,
        ned_preferred_name=ned_preferred_name,
    )

    candidates = [
        ("label_de", label_de),
        ("alias_de", alias_de),
        ("wiki_de_title", wiki_de_title),
        ("display_name", display_name),
        ("label_en", label_en),
        ("alias_en", alias_en),
        ("wiki_en_title", wiki_en_title),
        ("simbad_main_id", simbad_main_id),
        ("ned_preferred_name", ned_preferred_name),
        ("canonical_name", canonical_name),
    ]

    scored = []
    seen = set()

    for source, value in candidates:
        normalized = normalize_name_text(normalize_catalog_name(value))
        if not normalized:
            continue

        compact = lower_compact(normalized)
        if compact in seen:
            continue
        seen.add(compact)

        score = rank_name(
            normalized,
            source=source,
            canonical_name=canonical_name,
            simbad_main_id=simbad_main_id,
            ned_preferred_name=ned_preferred_name,
        )
        scored.append((score, source, normalized))

    if not scored:
        return ""

    scored.sort(key=lambda item: (-item[0], len(item[2]), item[2].lower()))
    return scored[0][2]
