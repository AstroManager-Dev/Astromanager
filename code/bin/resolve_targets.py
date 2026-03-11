#!/usr/bin/env python3
import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

DB_PATH = os.environ.get("DB_PATH", "/runtime/pipeline.db")
TIMEOUT = float(os.environ.get("TARGET_RESOLVER_TIMEOUT", "20"))
USER_AGENT = os.environ.get("TARGET_RESOLVER_UA", "AstroManager/1.0")
SESAME_BASE = os.environ.get("TARGET_RESOLVER_SESAME_BASE", "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/")

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_name(name: str) -> str:
    return " ".join((name or "").strip().split())

def build_url(ident: str) -> str:
    ident = normalize_name(ident)
    if not ident:
        raise ValueError("empty identifier")
    return SESAME_BASE + "?" + urllib.parse.quote_plus(ident)

def http_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/xml,text/xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")

def extract_xml_document(raw_text: str) -> str:
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    start = raw_text.find("<?xml")
    if start == -1:
        start = raw_text.find("<Sesame")
    if start == -1:
        raise ValueError("no xml start tag found")
    end = raw_text.rfind("</Sesame>")
    if end == -1:
        raise ValueError("no closing </Sesame> tag found")
    end += len("</Sesame>")
    xml_text = raw_text[start:end].strip()
    if not xml_text:
        raise ValueError("empty xml fragment after extraction")
    return xml_text

def sesame_text(root: ET.Element, path: str) -> str:
    node = root.find(path)
    if node is None or node.text is None:
        return ""
    return normalize_name(node.text)

def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None

def parse_sesame_xml(xml_text: str) -> dict[str, Any]:
    xml_text = extract_xml_document(xml_text)
    root = ET.fromstring(xml_text)
    target = root.find(".//Target")
    chosen = target if target is not None else root
    resolver = chosen.find(".//Resolver")
    chosen2 = resolver if resolver is not None else chosen
    aliases: list[str] = []
    for path in (".//oname", ".//alias", ".//id", ".//obj", ".//name"):
        for node in chosen2.findall(path):
            if node.text:
                value = normalize_name(node.text)
                if value and value not in aliases:
                    aliases.append(value)
    main_id = aliases[0] if aliases else ""
    return {
        "main_id": main_id,
        "aliases": aliases,
        "ra_deg": parse_float(sesame_text(chosen2, ".//jradeg")),
        "dec_deg": parse_float(sesame_text(chosen2, ".//jdedeg")),
        "coord_text": sesame_text(chosen2, ".//jpos"),
        "coord_ref": sesame_text(chosen2, ".//refPos"),
        "otype": sesame_text(chosen2, ".//otype"),
        "otype_txt": sesame_text(chosen2, ".//otype_txt"),
        "xml_size": len(xml_text),
    }

def is_system_target(canonical_name: str, category: str) -> bool:
    canonical = normalize_name(canonical_name).lower()
    category = normalize_name(category).lower()
    return category in {"sun", "moon"} or canonical in {"sun", "moon"}

def select_targets(conn: sqlite3.Connection, only_new: bool, limit: int) -> list[sqlite3.Row]:
    if only_new:
        sql = """
        SELECT id, canonical_name, display_name, category, coord_status, name_status
          FROM targets
         WHERE COALESCE(coord_status,'pending') IN ('pending','error')
           AND LOWER(COALESCE(category,'')) NOT IN ('sun','moon')
           AND LOWER(TRIM(COALESCE(canonical_name,''))) NOT IN ('sun','moon')
         ORDER BY id ASC
         LIMIT ?
        """
    else:
        sql = """
        SELECT id, canonical_name, display_name, category, coord_status, name_status
          FROM targets
         WHERE LOWER(COALESCE(category,'')) NOT IN ('sun','moon')
           AND LOWER(TRIM(COALESCE(canonical_name,''))) NOT IN ('sun','moon')
         ORDER BY id ASC
         LIMIT ?
        """
    return conn.execute(sql, (limit,)).fetchall()

def mark_system_target(conn: sqlite3.Connection, target_id: int) -> None:
    conn.execute(
        """
        UPDATE targets
           SET coord_status='fixed_system_target',
               name_status='fixed_system_target',
               coord_source='system',
               name_source='system',
               name_resolved_at=datetime('now'),
               updated_at=datetime('now')
         WHERE id=?
        """,
        (target_id,),
    )
    conn.commit()

def mark_error(conn: sqlite3.Connection, target_id: int, message: str, payload: Any | None = None) -> None:
    data = {"error": message}
    if payload is not None:
        data["payload"] = payload
    conn.execute(
        """
        UPDATE targets
           SET coord_status='error',
               coord_source='sesame',
               updated_at=datetime('now')
         WHERE id=?
        """,
        (json.dumps(data, ensure_ascii=False), target_id),
    )
    conn.commit()

def update_target(conn: sqlite3.Connection, target_id: int, canonical_name: str, parsed: dict[str, Any], payload: Any) -> None:
    display_name = normalize_name(canonical_name)
    name_status = "pending"
    conn.execute(
        """
        UPDATE targets
           SET display_name=?,
               coord_status='resolved',
               name_status=?,
               coord_source='sesame',
               ra_deg=?,
               dec_deg=?,
               coord_text=?,
               coord_ref=?,
               updated_at=datetime('now')
         WHERE id=?
        """,
        (
            display_name,
            name_status,
            parsed.get("ra_deg"),
            parsed.get("dec_deg"),
            normalize_name(str(parsed.get("coord_text", ""))),
            normalize_name(str(parsed.get("coord_ref", ""))),
            target_id,
        ),
    )
    conn.commit()

def resolve_one(conn: sqlite3.Connection, row: sqlite3.Row) -> None:
    target_id = int(row["id"])
    canonical_name = normalize_name(str(row["canonical_name"] or ""))
    category = normalize_name(str(row["category"] or ""))
    if not canonical_name:
        mark_error(conn, target_id, "empty canonical_name")
        return
    if is_system_target(canonical_name, category):
        mark_system_target(conn, target_id)
        return
    url = build_url(canonical_name)
    try:
        raw_text = http_get_text(url)
    except Exception as exc:
        mark_error(conn, target_id, f"http_error: {exc}")
        return
    try:
        parsed = parse_sesame_xml(raw_text)
    except Exception as exc:
        mark_error(conn, target_id, f"xml_parse_error: {exc}", {"raw_head": raw_text[:1000]})
        return
    payload = {"query": canonical_name, "url": url, "parsed": parsed}
    update_target(conn, target_id, canonical_name, parsed, payload)

def main() -> int:
    only_new = "--all" not in sys.argv
    limit = 1000
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = max(1, int(sys.argv[idx + 1]))
    conn = db()
    try:
        rows = select_targets(conn, only_new=only_new, limit=limit)
        print(f"targets_to_resolve={len(rows)}")
        for row in rows:
            print(f"resolving id={row['id']} canonical_name={row['canonical_name']}")
            resolve_one(conn, row)
            time.sleep(0.25)
    finally:
        conn.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
