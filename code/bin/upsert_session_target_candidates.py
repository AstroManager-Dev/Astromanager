#!/usr/bin/env python3
import json
import math
import re
import sqlite3
import sys

payload = json.loads(sys.argv[1])
db_path = sys.argv[2]
session_key = sys.argv[3]

MATCH_RADIUS_DEG = 0.20


def norm_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def canonical_target_name(value: str) -> str:
    s = norm_text(value).lower()
    if not s:
        return ""

    s = re.sub(r"\s+", " ", s).strip()

    if s in {"unknown", "sun", "moon"}:
        return s

    m = re.match(r"^(?:messier|m)\s*0*([0-9]+)$", s, re.I)
    if m:
        return f"m{int(m.group(1))}"

    m = re.match(r"^(?:ngc|new general catalogue)\s*0*([0-9]+)([a-z]?)$", s, re.I)
    if m:
        return f"ngc{int(m.group(1)):04d}{m.group(2).lower()}"

    m = re.match(r"^(?:ic)\s*0*([0-9]+)([a-z]?)$", s, re.I)
    if m:
        return f"ic{int(m.group(1))}{m.group(2).lower()}"

    s = s.replace(" ", "")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def display_catalog_name(value: str) -> str:
    c = canonical_target_name(value)
    if not c:
        return ""

    if c == "unknown":
        return "unknown"
    if c == "sun":
        return "Sun"
    if c == "moon":
        return "Moon"

    m = re.match(r"^m([0-9]+)$", c)
    if m:
        return f"Messier {int(m.group(1))}"

    m = re.match(r"^ngc0*([0-9]+)([a-z]?)$", c)
    if m:
        suffix = m.group(2).upper()
        return f"NGC {int(m.group(1))}{suffix}"

    m = re.match(r"^ic([0-9]+)([a-z]?)$", c)
    if m:
        suffix = m.group(2).upper()
        return f"IC {int(m.group(1))}{suffix}"

    return norm_text(value)


def angular_sep_deg(ra1, dec1, ra2, dec2):
    if None in (ra1, dec1, ra2, dec2):
        return None
    ra1r = math.radians(float(ra1))
    dec1r = math.radians(float(dec1))
    ra2r = math.radians(float(ra2))
    dec2r = math.radians(float(dec2))
    cos_sep = (
        math.sin(dec1r) * math.sin(dec2r) +
        math.cos(dec1r) * math.cos(dec2r) * math.cos(ra1r - ra2r)
    )
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def table_cols(table: str):
    return {r["name"] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}


targets_cols = table_cols("targets")
session_targets_cols = table_cols("session_targets")

cur.execute("SELECT id FROM sessions WHERE session_key=?", (session_key,))
row = cur.fetchone()
if not row:
    raise SystemExit(0)
session_id = row["id"]

cur.execute("DELETE FROM session_targets WHERE session_id=?", (session_id,))


def fetch_targets():
    return cur.execute("SELECT * FROM targets").fetchall()


def find_existing_target(candidate_names, ra_deg, dec_deg):
    targets = fetch_targets()

    canonical_candidates = []
    display_candidates = []

    for name in candidate_names:
        c = canonical_target_name(name)
        d = display_catalog_name(name)
        if c and c not in canonical_candidates:
            canonical_candidates.append(c)
        if d and d.lower() not in [x.lower() for x in display_candidates]:
            display_candidates.append(d)

    # 1) canonical_name exact
    if "canonical_name" in targets_cols:
        for t in targets:
            cn = canonical_target_name(t["canonical_name"])
            if cn and cn in canonical_candidates:
                return t["id"]

    # 2) slug exact
    if "slug" in targets_cols:
        for t in targets:
            slug = canonical_target_name(t["slug"])
            if slug and slug in canonical_candidates:
                return t["id"]

    # 3) display_name exact, canonicalisiert verglichen
    if "display_name" in targets_cols:
        for t in targets:
            dn_c = canonical_target_name(t["display_name"])
            if dn_c and dn_c in canonical_candidates:
                return t["id"]
        for t in targets:
            dn = norm_text(t["display_name"]).lower()
            if dn and dn in [x.lower() for x in display_candidates]:
                return t["id"]

    # 4) coordinate proximity fallback
    if "ra_deg" in targets_cols and "dec_deg" in targets_cols and ra_deg is not None and dec_deg is not None:
        best_id = None
        best_dist = None
        for t in targets:
            d = angular_sep_deg(t["ra_deg"], t["dec_deg"], ra_deg, dec_deg)
            if d is None:
                continue
            if d <= MATCH_RADIUS_DEG and (best_dist is None or d < best_dist):
                best_dist = d
                best_id = t["id"]
        if best_id is not None:
            return best_id

    return None


def upsert_target(candidate_names, display_name, category, object_type, ra_deg, dec_deg, angular_size_arcmin):
    primary_canonical = ""
    for n in candidate_names:
        c = canonical_target_name(n)
        if c:
            primary_canonical = c
            break

    if not primary_canonical:
        primary_canonical = canonical_target_name(display_name)

    if not primary_canonical:
        return None

    final_display_name = display_catalog_name(display_name or primary_canonical)
    if not final_display_name:
        final_display_name = display_catalog_name(primary_canonical)

    existing_id = find_existing_target(candidate_names + [display_name, primary_canonical, final_display_name], ra_deg, dec_deg)

    values = {}
    if "slug" in targets_cols:
        values["slug"] = primary_canonical
    if "canonical_name" in targets_cols:
        values["canonical_name"] = primary_canonical
    if "display_name" in targets_cols:
        values["display_name"] = final_display_name
    if "category" in targets_cols:
        values["category"] = category or "unknown"
    if "object_type" in targets_cols:
        values["object_type"] = object_type
    if "ra_deg" in targets_cols:
        values["ra_deg"] = ra_deg
    if "dec_deg" in targets_cols:
        values["dec_deg"] = dec_deg
    if "angular_size_arcmin" in targets_cols:
        values["angular_size_arcmin"] = angular_size_arcmin
    if "source" in targets_cols:
        values["source"] = "platesolve_field_match"

    if existing_id is not None:
        sets = []
        params = []

        for col, val in values.items():
            if col == "display_name":
                sets.append(f"{col}=CASE WHEN COALESCE({col},'')='' THEN ? ELSE {col} END")
                params.append(val)
            elif col in ("ra_deg", "dec_deg", "angular_size_arcmin", "object_type"):
                sets.append(f"{col}=COALESCE({col}, ?)")
                params.append(val)
            elif col in ("slug", "canonical_name", "category", "source"):
                sets.append(f"{col}=CASE WHEN COALESCE({col},'')='' THEN ? ELSE {col} END")
                params.append(val)

        if "updated_at" in targets_cols:
            sets.append("updated_at=datetime('now')")

        if sets:
            params.append(existing_id)
            cur.execute(f"UPDATE targets SET {', '.join(sets)} WHERE id=?", params)

        return existing_id

    insert_cols = []
    insert_vals = []
    insert_params = []

    for col, val in values.items():
        insert_cols.append(col)
        insert_vals.append("?")
        insert_params.append(val)

    if "created_at" in targets_cols:
        insert_cols.append("created_at")
        insert_vals.append("datetime('now')")
    if "updated_at" in targets_cols:
        insert_cols.append("updated_at")
        insert_vals.append("datetime('now')")

    cur.execute(
        f"INSERT INTO targets ({', '.join(insert_cols)}) VALUES ({', '.join(insert_vals)})",
        insert_params,
    )
    return cur.lastrowid


for item in payload.get("candidates", []):
    target_name = norm_text(item.get("target_name") or "")
    display_name = norm_text(item.get("display_name") or target_name)
    object_type = norm_text(item.get("object_type") or "")
    ra_deg = item.get("ra_deg")
    dec_deg = item.get("dec_deg")
    angular_size_arcmin = item.get("angular_size_arcmin")
    category = "deepsky"

    candidate_names = []
    for raw in [display_name, target_name]:
        c = canonical_target_name(raw)
        if c and c not in candidate_names:
            candidate_names.append(c)

    target_id = upsert_target(
        candidate_names=candidate_names,
        display_name=display_name,
        category=category,
        object_type=object_type,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        angular_size_arcmin=angular_size_arcmin,
    )

    st_cols = []
    st_vals = []
    st_params = []

    def add_st(col, val):
        if col in session_targets_cols:
            st_cols.append(col)
            st_vals.append("?")
            st_params.append(val)

    add_st("session_id", session_id)
    add_st("target_id", target_id)
    add_st("target_name", target_name)
    add_st("object_type", object_type)
    add_st("source", "platesolve_field_match")
    add_st("is_requested_target", int(item.get("is_requested_target", 0)))
    add_st("is_primary", int(item.get("is_primary", 0)))
    add_st("is_major", int(item.get("is_major", 0)))
    add_st("priority_rank", item.get("priority_rank"))
    add_st("score", item.get("score"))
    add_st("distance_to_center_deg", item.get("distance_to_center_deg"))
    add_st("in_frame_fraction", item.get("in_frame_fraction"))
    add_st("angular_size_arcmin", angular_size_arcmin)
    add_st("ra_deg", ra_deg)
    add_st("dec_deg", dec_deg)
    add_st("notes", display_catalog_name(display_name) or display_name)

    cur.execute(
        f"INSERT INTO session_targets ({', '.join(st_cols)}) VALUES ({', '.join(st_vals)})",
        st_params,
    )

conn.commit()
conn.close()
