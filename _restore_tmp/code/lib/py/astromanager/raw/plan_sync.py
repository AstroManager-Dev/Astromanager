#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import asdict, dataclass

from .constants import RAW_SOURCE_KEY_DEFAULT
from .device_source import load_device_source
from .sync_decider import KnownFile, RemoteMeta, decide_sync_action

@dataclass(frozen=True)
class PlanEntry:
    action: str
    reason: str
    remote_path: str
    local_abs_path: str
    rel_path: str
    size_bytes: int
    mtime_epoch: int
    known_status: str
    known_sha256: str


def _load_known_files(db_path: str, source_id: int) -> dict[str, KnownFile]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT abs_path, rel_path, size_bytes, mtime_epoch, sha256, file_status, is_current
            FROM raw_files
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchall()
    finally:
        conn.close()
    return {
        str(row["rel_path"]): KnownFile(
            abs_path=str(row["abs_path"]),
            rel_path=str(row["rel_path"]),
            size_bytes=int(row["size_bytes"]),
            mtime_epoch=int(row["mtime_epoch"]),
            sha256=str(row["sha256"]),
            file_status=str(row["file_status"]),
            is_current=int(row["is_current"]),
        )
        for row in rows
    }


def _local_rel_path(raw_root: str, remote_path: str) -> tuple[str, str]:
    rel_path = remote_path.lstrip("/")
    local_abs_path = os.path.join(raw_root.rstrip("/"), rel_path)
    return rel_path, local_abs_path


def build_plan(db_path: str, inventory_json: str, raw_root: str, source_key: str) -> dict:
    source = load_device_source(db_path, source_key)
    known = _load_known_files(db_path, source.id)
    with open(inventory_json, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    items = payload.get("items", [])
    plan_items: list[dict] = []
    counters: dict[str, int] = {}
    for item in items:
        rel_path, local_abs_path = _local_rel_path(raw_root, item["remote_path"])
        remote = RemoteMeta(
            remote_path=str(item["remote_path"]),
            remote_dir=str(item["remote_dir"]),
            file_name=str(item["file_name"]),
            size_bytes=int(item.get("size_bytes", -1)),
            mtime_epoch=int(item.get("mtime_epoch", 0)),
            local_abs_path=local_abs_path,
            rel_path=rel_path,
        )
        known_row = known.get(rel_path)
        action, reason = decide_sync_action(known_row, remote)
        entry = PlanEntry(
            action=action,
            reason=reason,
            remote_path=remote.remote_path,
            local_abs_path=remote.local_abs_path,
            rel_path=remote.rel_path,
            size_bytes=remote.size_bytes,
            mtime_epoch=remote.mtime_epoch,
            known_status=(known_row.file_status if known_row else ""),
            known_sha256=(known_row.sha256 if known_row else ""),
        )
        plan_items.append(asdict(entry))
        counters[action] = counters.get(action, 0) + 1
    return {
        "source_key": source.source_key,
        "source_id": source.id,
        "inventory_count": len(items),
        "plan_count": len(plan_items),
        "counters": counters,
        "items": plan_items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build RAW sync plan from DB and remote inventory")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--inventory-json", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--source-key", default=RAW_SOURCE_KEY_DEFAULT)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args(argv)
    payload = build_plan(args.db_path, args.inventory_json, args.raw_root, args.source_key)
    with open(args.output_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"plan_count={payload['plan_count']}")
    for key in sorted(payload["counters"]):
        print(f"plan_{key}={payload['counters'][key]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
