#!/usr/bin/env python3

def _norm(value) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def normalize_distance_to_ly(value, unit_qid="", unit_label_de="", unit_label_en=""):
    if value is None:
        return None, ""

    try:
        numeric = float(value)
    except Exception:
        return None, ""

    qid = _norm(unit_qid)
    label_de = _norm(unit_label_de)
    label_en = _norm(unit_label_en)

    candidates = {
        qid,
        label_de,
        label_en,
    }

    # bekannte Wikidata-QIDs / Textformen
    if candidates & {
        "q1811",  # astronomical unit
        "astronomical unit",
        "astronomische einheit",
        "au",
    }:
        return numeric * 0.000015812507409, "Lichtjahr"

    if candidates & {
        "q12129",  # parsec
        "parsec",
        "pc",
    }:
        return numeric * 3.26156, "Lichtjahr"

    if candidates & {
        "kiloparsec",
        "kpc",
    }:
        return numeric * 3261.56, "Lichtjahr"

    if candidates & {
        "q3773454",  # megaparsec
        "megaparsec",
        "mpc",
    }:
        return numeric * 3261560.0, "Lichtjahr"

    if candidates & {
        "lichtjahr",
        "lichtjahre",
        "light-year",
        "light-years",
        "ly",
    }:
        return numeric, "Lichtjahr"

    return None, ""
