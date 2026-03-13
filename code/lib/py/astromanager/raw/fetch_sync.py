#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from ftplib import FTP

from .constants import (
    RAW_PLAN_DOWNLOAD_NEW,
    RAW_PLAN_REPLACE_CHANGED,
    RAW_PLAN_REPLACE_DEFECTIVE,
    RAW_PLAN_RESTORE_MISSING_LOCAL,
    RAW_SOURCE_KEY_DEFAULT,
)
from .device_source import load_device_source

DOWNLOAD_ACTIONS = {
    RAW_PLAN_DOWNLOAD_NEW,
    RAW_PLAN_RESTORE_MISSING_LOCAL,
    RAW_PLAN_REPLACE_CHANGED,
    RAW_PLAN_REPLACE_DEFECTIVE,
}


def _connect(host: str, user: str, password: str, timeout: int) -> FTP:
    ftp = FTP()
    ftp.connect(host=host, port=21, timeout=timeout)
    ftp.login(user=user, passwd=password)
    ftp.set_pasv(True)
    return ftp


def _sha256_of_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _write_summary(db_path: str, summary_key: str, payload: dict) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO app_state(key, value, updated_at)
            VALUES(?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')
            """,
            (summary_key, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
        )
        conn.commit()
    finally:
        conn.close()


def execute_plan(db_path: str, source_key: str, host: str, user: str, password: str, timeout: int, plan_json: str, result_json: str, dry_run: bool) -> dict:
    _ = load_device_source(db_path, source_key)
    with open(plan_json, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    items = payload.get("items", [])
    results = []
    counters = {"downloaded": 0, "skipped": 0, "errors": 0}
    ftp = None if dry_run else _connect(host, user, password, timeout)
    try:
        for item in items:
            action = item["action"]
            if action not in DOWNLOAD_ACTIONS:
                counters["skipped"] += 1
                results.append({"action": action, "result": "skipped", "rel_path": item["rel_path"]})
                continue
            if dry_run:
                results.append({"action": action, "result": "dry_run", "rel_path": item["rel_path"]})
                continue
            local_abs = item["local_abs_path"]
            os.makedirs(os.path.dirname(local_abs), exist_ok=True)
            tmp_abs = local_abs + ".part"
            try:
                with open(tmp_abs, "wb") as fh:
                    ftp.retrbinary(f"RETR {item['remote_path']}", fh.write)
                os.replace(tmp_abs, local_abs)
                sha256 = _sha256_of_file(local_abs)
                if int(item.get("mtime_epoch", 0)) > 0:
                    os.utime(local_abs, (int(item["mtime_epoch"]), int(item["mtime_epoch"])))
                results.append({
                    "action": action,
                    "result": "downloaded",
                    "rel_path": item["rel_path"],
                    "local_abs_path": local_abs,
                    "sha256": sha256,
                    "size_bytes": os.path.getsize(local_abs),
                    "mtime_epoch": int(os.path.getmtime(local_abs)),
                })
                counters["downloaded"] += 1
            except Exception as exc:
                counters["errors"] += 1
                results.append({"action": action, "result": "error", "rel_path": item["rel_path"], "error": str(exc)})
                try:
                    if os.path.exists(tmp_abs):
                        os.remove(tmp_abs)
                except Exception:
                    pass
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                pass
    result_payload = {"counters": counters, "items": results}
    with open(result_json, "w", encoding="utf-8") as fh:
        json.dump(result_payload, fh, ensure_ascii=False, separators=(",", ":"))
    _write_summary(db_path, "raw_sync_last_result", result_payload)
    return result_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute RAW sync download plan")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--source-key", default=RAW_SOURCE_KEY_DEFAULT)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="anonymous")
    parser.add_argument("--password", default="")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    result = execute_plan(args.db_path, args.source_key, args.host, args.user, args.password, args.timeout, args.plan_json, args.result_json, args.dry_run)
    print(f"downloaded={result['counters']['downloaded']}")
    print(f"skipped={result['counters']['skipped']}")
    print(f"errors={result['counters']['errors']}")
    return 0 if result['counters']['errors'] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
