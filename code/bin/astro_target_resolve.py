#!/usr/bin/env python3
import csv
import json
import math
import sys
from pathlib import Path

from astropy.coordinates import Angle
import astropy.units as u


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def parse_ra(value: str) -> float:
    s = (value or "").strip()
    if not s:
        raise ValueError("empty RA")
    if ":" in s:
        return float(Angle(s, unit=u.hourangle).deg)
    return float(s)


def parse_dec(value: str) -> float:
    s = (value or "").strip()
    if not s:
        raise ValueError("empty Dec")
    if ":" in s:
        return float(Angle(s, unit=u.deg).deg)
    return float(s)


def angsep_deg(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, [ra1, dec1, ra2, dec2])
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    c = min(1.0, max(-1.0, c))
    return float(math.degrees(math.acos(c)))


def pref_name(row: dict) -> str:
    m = (row.get("M") or "").strip()
    if m:
        try:
            return f"m{int(m)}"
        except Exception:
            pass
    name = (row.get("Name") or "").strip().lower().replace(" ", "")
    return name or "unknown"


def object_type(row: dict) -> str:
    return (row.get("Type") or "").strip().lower()


def load_catalog(csv_path: str) -> list[dict]:
    items: list[dict] = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = (row.get("Name") or "").strip()
            if not name:
                continue
            try:
                ra = parse_ra(row.get("RA", ""))
                dec = parse_dec(row.get("Dec", ""))
            except Exception:
                continue
            try:
                maj = float(((row.get("MajAx") or "0").strip()) or "0")
            except Exception:
                maj = 0.0

            items.append(
                {
                    "target_name": pref_name(row),
                    "display_name": name,
                    "object_type": object_type(row),
                    "ra_deg": ra,
                    "dec_deg": dec,
                    "angular_size_arcmin": maj,
                }
            )
    return items


def normalize_target_raw(target_raw: str) -> str:
    s = (target_raw or "").strip().lower()
    s = s.replace(" ", "")
    if s in {"unknown", "sun", "moon", ""}:
        return s
    if s.startswith("m") and s[1:].isdigit():
        return f"m{int(s[1:])}"
    if s.isdigit():
        return f"m{int(s)}"
    return s


def main() -> None:
    if len(sys.argv) != 9:
        die(
            "usage: astro_target_resolve.py <opengc.csv> <center_ra> <center_dec> <radius_deg> "
            "<target_raw> <secondary_frac> <secondary_min_arcmin> <max_candidates>"
        )

    csv_path = sys.argv[1]
    center_ra = float(sys.argv[2])
    center_dec = float(sys.argv[3])
    radius_deg = float(sys.argv[4])
    target_raw = normalize_target_raw(sys.argv[5])
    secondary_frac = float(sys.argv[6])
    secondary_min_arcmin = float(sys.argv[7])
    max_candidates = int(sys.argv[8])

    if not Path(csv_path).is_file():
        die(f"catalog not found: {csv_path}")

    catalog = load_catalog(csv_path)

    candidates: list[dict] = []
    for item in catalog:
        sep = angsep_deg(center_ra, center_dec, item["ra_deg"], item["dec_deg"])
        if sep <= radius_deg:
            row = dict(item)
            row["distance_to_center_deg"] = sep
            candidates.append(row)

    candidates.sort(key=lambda x: (-x["angular_size_arcmin"], x["distance_to_center_deg"]))
    candidates = candidates[:max_candidates]

    if not candidates:
        print(json.dumps({
            "target_final": "unknown",
            "target_strategy": "field_review",
            "field_object_count": 0,
            "requested_target_found": 0,
            "target_conflict_flag": 0,
            "target_conflict_note": "no catalog candidates in field radius",
            "candidates": []
        }, ensure_ascii=False))
        return

    top1 = candidates[0]
    top1_size = max(float(top1["angular_size_arcmin"]), 0.0)

    majors: list[dict] = []
    seen = set()
    for item in candidates:
        name = item["target_name"]
        if name in seen:
            continue
        if not majors:
            majors.append(item)
            seen.add(name)
            continue

        size_ok = item["angular_size_arcmin"] >= (secondary_frac * top1_size)
        abs_ok = item["angular_size_arcmin"] >= secondary_min_arcmin
        if size_ok or abs_ok:
            majors.append(item)
            seen.add(name)
        if len(majors) >= 2:
            break

    if len(majors) == 1:
        target_final = majors[0]["target_name"]
        target_strategy = "single_primary"
    else:
        target_final = "_".join([m["target_name"] for m in majors])
        target_strategy = "dual_primary"

    requested_found = 1 if target_raw and any(c["target_name"] == target_raw for c in candidates) else 0
    conflict = 1 if target_raw not in {"", "unknown", "sun", "moon"} and requested_found == 0 else 0
    conflict_note = ""
    if conflict:
        conflict_note = f"target_raw={target_raw} not found in solved field candidates"

    for idx, item in enumerate(candidates, start=1):
        item["priority_rank"] = idx
        item["is_requested_target"] = 1 if target_raw and item["target_name"] == target_raw else 0
        item["is_primary"] = 1 if item["target_name"] == top1["target_name"] else 0
        item["is_major"] = 1 if any(m["target_name"] == item["target_name"] for m in majors) else 0
        size = max(item["angular_size_arcmin"], 0.1)
        dist = max(item["distance_to_center_deg"], 0.01)
        item["score"] = round((size / dist), 6)
        item["in_frame_fraction"] = 1.0

    out = {
        "target_final": target_final,
        "target_strategy": target_strategy,
        "field_object_count": len(candidates),
        "requested_target_found": requested_found,
        "target_conflict_flag": conflict,
        "target_conflict_note": conflict_note,
        "candidates": candidates,
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
