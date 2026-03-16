#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("DB_PATH", "/runtime/pipeline.db"))
NEVER_RESET_FILE = Path(os.environ.get("DB_NEVER_RESET_FILE", "/config/db_never_reset_tables.txt"))
RUNTIME_ROOT = Path(os.environ.get("RUNTIME_ROOT", "/runtime"))
LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))

INDEX_STATE_SUBDIRS = [
    "cali_frame",
    "dwarf_dark",
    "light_sessions",
    "plate_solve",
]

WEB_PROGRESS_CACHE = RUNTIME_ROOT / "web_progress_cache.json"
FACTORY_RESET_MARKER = RUNTIME_ROOT / "last_factory_reset.ts"
WEBUI_LOG = LOG_ROOT / "master" / "webui.log"
STEPS_LOG_DIR = LOG_ROOT / "steps"


def read_never_reset_tables(path: Path) -> set[str]:
    if not path.exists():
        return set()

    tables: set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        tables.add(line)
    return tables


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row[0] for row in rows]


def reset_tables(
    conn: sqlite3.Connection,
    keep_tables: set[str],
    dry_run: bool,
    vacuum: bool,
) -> tuple[list[str], list[str]]:
    all_tables = list_tables(conn)
    wipe_tables = [t for t in all_tables if t not in keep_tables]

    print(f"DB: {DB_PATH}")
    print(f"Never-reset-Datei: {NEVER_RESET_FILE}")
    print(f"Gefundene Tabellen: {len(all_tables)}")
    print(f"Behalten: {len(keep_tables & set(all_tables))}")
    print(f"Resetten: {len(wipe_tables)}")
    print()

    print("Tabellen, die erhalten bleiben:")
    kept = sorted(keep_tables & set(all_tables))
    if kept:
        for table in kept:
            print(f"  KEEP  {table}")
    else:
        print("  (keine)")
    print()

    print("Tabellen, die geleert werden:")
    if wipe_tables:
        for table in wipe_tables:
            print(f"  WIPE  {table}")
    else:
        print("  (keine)")
    print()

    if dry_run:
        print("DRY-RUN: Keine DB-Änderungen durchgeführt.")
        return all_tables, wipe_tables

    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=OFF;")

    for table in wipe_tables:
        cur.execute(f'DELETE FROM "{table}";')

    seq_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
    ).fetchone()
    if seq_exists:
        for table in wipe_tables:
            cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))

    conn.commit()

    if vacuum:
        print("Führe VACUUM aus ...")
        cur.execute("VACUUM;")
        conn.commit()

    print("DB-Reset abgeschlossen.")
    return all_tables, wipe_tables


def wipe_dir_contents(path: Path, dry_run: bool) -> None:
    if not path.exists():
        print(f"  MISS  {path}")
        return

    print(f"  WIPE  {path}/*")
    if dry_run:
        return

    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except FileNotFoundError:
                pass


def wipe_path(path: Path, dry_run: bool) -> None:
    if not path.exists() and not path.is_symlink():
        print(f"  MISS  {path}")
        return

    print(f"  WIPE  {path}")
    if dry_run:
        return

    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def wipe_logs(dry_run: bool) -> None:
    print()
    print("Log-/Cache-Reset:")
    wipe_path(WEB_PROGRESS_CACHE, dry_run)

    if WEBUI_LOG.exists():
        print(f"  TRUNC {WEBUI_LOG}")
        if not dry_run:
            WEBUI_LOG.parent.mkdir(parents=True, exist_ok=True)
            WEBUI_LOG.write_text("", encoding="utf-8")
    else:
        print(f"  MISS  {WEBUI_LOG}")

    if STEPS_LOG_DIR.exists():
        print(f"  WIPE  {STEPS_LOG_DIR}/*")
        if not dry_run:
            for child in STEPS_LOG_DIR.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    try:
                        child.unlink()
                    except FileNotFoundError:
                        pass
    else:
        print(f"  MISS  {STEPS_LOG_DIR}")

    print(f"  WRITE {FACTORY_RESET_MARKER}")
    if not dry_run:
        FACTORY_RESET_MARKER.parent.mkdir(parents=True, exist_ok=True)
        FACTORY_RESET_MARKER.write_text(str(int(time.time())), encoding="utf-8")


def reset_runtime_state(dry_run: bool, keep_runtime_state: bool) -> None:
    print()
    print(f"Runtime-Root: {RUNTIME_ROOT}")

    if keep_runtime_state:
        print("Runtime-State bleibt erhalten (--keep-runtime-state).")
        return

    index_root = RUNTIME_ROOT / "index_sessions"
    ok_path = RUNTIME_ROOT / "ok"

    print("Runtime-State-Pfade:")
    print(f"  ROOT  {index_root}")
    for sub in INDEX_STATE_SUBDIRS:
        wipe_dir_contents(index_root / sub, dry_run)

    wipe_path(ok_path, dry_run)

    if dry_run:
        print("DRY-RUN: Keine Runtime-State-Dateien gelöscht.")
        return

    index_root.mkdir(parents=True, exist_ok=True)
    for sub in INDEX_STATE_SUBDIRS:
        (index_root / sub).mkdir(parents=True, exist_ok=True)

    print("Runtime-State zurückgesetzt.")
    print("Leere State-Unterordner neu angelegt:")
    for sub in INDEX_STATE_SUBDIRS:
        print(f"  MKDIR {index_root / sub}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Leert alle DB-Tabellen außer Never-Reset-Tabellen und setzt Runtime-State/Logs auf Werkszustand zurück."
    )
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, was gelöscht würde.")
    parser.add_argument("--vacuum", action="store_true", help="Nach dem Reset VACUUM ausführen.")
    parser.add_argument(
        "--keep-runtime-state",
        action="store_true",
        help="Runtime-State-Dateien unter /runtime nicht löschen.",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"FEHLER: DB nicht gefunden: {DB_PATH}", file=sys.stderr)
        return 1

    keep_tables = read_never_reset_tables(NEVER_RESET_FILE)

    conn = sqlite3.connect(DB_PATH)
    try:
        reset_tables(
            conn=conn,
            keep_tables=keep_tables,
            dry_run=args.dry_run,
            vacuum=args.vacuum,
        )
    finally:
        conn.close()

    reset_runtime_state(
        dry_run=args.dry_run,
        keep_runtime_state=args.keep_runtime_state,
    )

    wipe_logs(args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
