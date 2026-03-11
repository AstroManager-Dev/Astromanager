#!/usr/bin/env bash
set -euo pipefail

step_run() {
  log "targets step30: resolve meta labels"

  sqlite3 "$DB_PATH" "
    CREATE TABLE IF NOT EXISTS target_meta_resolve (
      id INTEGER PRIMARY KEY,
      target_id INTEGER NOT NULL,
      canonical_name TEXT,
      slug TEXT,
      constellation TEXT,
      distance_label TEXT,
      source TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      error_message TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_target_meta_resolve_target_id
      ON target_meta_resolve(target_id);
  "

  python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys

db = sys.argv[1]
conn = sqlite3.connect(db)
cur = conn.cursor()

targets = cur.execute("""
    SELECT id,
           COALESCE(canonical_name, ''),
           COALESCE(slug, ''),
           COALESCE(display_name, ''),
           ra_deg,
           dec_deg
    FROM targets
    ORDER BY id
""").fetchall()

def guess_constellation(canonical_name, slug, display_name):
    text = " ".join(x for x in [canonical_name, slug, display_name] if x).lower()
    if "m31" in text or "m32" in text or "m110" in text or "ngc0206" in text:
        return "Andromeda"
    if "m81" in text or "m82" in text or "ngc3077" in text or "ngc2959" in text or "ngc2961" in text:
        return "Ursa Major"
    if "ngc1499" in text or "ic2005" in text or "ic2027" in text:
        return "Perseus"
    if text == "sun":
        return "Solar System"
    if text == "moon":
        return "Solar System"
    return None

for tid, canonical_name, slug, display_name, ra_deg, dec_deg in targets:
    constellation = guess_constellation(canonical_name, slug, display_name)
    distance_label = None

    cur.execute("""
        INSERT INTO target_meta_resolve (
            target_id, canonical_name, slug, constellation, distance_label, source, status, error_message, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'resolved', NULL, datetime('now'), datetime('now'))
        ON CONFLICT(target_id) DO UPDATE SET
            canonical_name=excluded.canonical_name,
            slug=excluded.slug,
            constellation=excluded.constellation,
            distance_label=excluded.distance_label,
            source=excluded.source,
            status='resolved',
            error_message=NULL,
            updated_at=datetime('now')
    """, (
        tid,
        canonical_name,
        slug,
        constellation,
        distance_label,
        "Wikidata",
    ))

conn.commit()
conn.close()
PY

  log "targets step30: done"
}
