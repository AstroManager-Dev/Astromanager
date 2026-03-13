#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import fnmatch
import json
import posixpath
from dataclasses import asdict, dataclass
from ftplib import FTP, error_perm
from typing import Iterator

from .constants import RAW_FITS_EXTENSIONS, RAW_REMOTE_BASE_DIR, RAW_SOURCE_KEY_DEFAULT
from .device_source import DeviceSource, load_device_source


@dataclass(frozen=True)
class RemoteFile:
    remote_path: str
    remote_dir: str
    file_name: str
    size_bytes: int
    mtime_epoch: int


def _connect(host: str, user: str, password: str, timeout: int) -> FTP:
    ftp = FTP()
    ftp.connect(host=host, port=21, timeout=timeout)
    ftp.login(user=user, passwd=password)
    ftp.set_pasv(True)
    return ftp


def _mtime_from_modify(raw: str) -> int:
    if len(raw) < 14 or not raw[:14].isdigit():
        return 0
    value = dt.datetime.strptime(raw[:14], "%Y%m%d%H%M%S")
    return calendar.timegm(value.utctimetuple())


def _list_dir_entries(ftp: FTP, base_dir: str) -> list[tuple[str, dict]]:
    try:
        return list(ftp.mlsd(base_dir))
    except Exception:
        entries: list[tuple[str, dict]] = []
        for child in ftp.nlst(base_dir):
            if child in (base_dir, ".", ".."):
                continue
            try:
                ftp.cwd(child)
                ftp.cwd("/")
                entries.append((posixpath.basename(child), {"type": "dir", "path": child}))
            except Exception:
                try:
                    size = int(ftp.size(child) or -1)
                except Exception:
                    size = -1
                entries.append((posixpath.basename(child), {"type": "file", "path": child, "size": str(size)}))
        return entries


def _iter_remote_files(ftp: FTP, base_dir: str) -> Iterator[RemoteFile]:
    for name, facts in _list_dir_entries(ftp, base_dir):
        child = facts.get("path") or posixpath.join(base_dir, name)
        kind = (facts.get("type") or "").lower()

        if kind == "dir":
            yield from _iter_remote_files(ftp, child)
            continue

        if kind not in ("", "file"):
            continue

        file_name = posixpath.basename(child)
        if not file_name.lower().endswith(RAW_FITS_EXTENSIONS):
            continue

        yield RemoteFile(
            remote_path=child,
            remote_dir=posixpath.dirname(child),
            file_name=file_name,
            size_bytes=int(facts.get("size") or -1),
            mtime_epoch=_mtime_from_modify(facts.get("modify") or ""),
        )


def _iter_matching_roots(ftp: FTP, source: DeviceSource) -> Iterator[str]:
    patterns = source.root_names
    for name, facts in _list_dir_entries(ftp, RAW_REMOTE_BASE_DIR):
        kind = (facts.get("type") or "").lower()
        if kind != "dir":
            continue
        dir_name = name or posixpath.basename(facts.get("path") or "")
        if not dir_name:
            continue
        if any(fnmatch.fnmatchcase(dir_name, pattern) for pattern in patterns):
            yield facts.get("path") or posixpath.join(RAW_REMOTE_BASE_DIR, dir_name)


def build_inventory(source: DeviceSource, host: str, user: str, password: str, timeout: int) -> dict:
    if source.protocol.lower() != "ftp":
        raise RuntimeError(f"unsupported protocol for initial RAW sync: {source.protocol}")

    ftp = _connect(host, user, password, timeout)
    try:
        items: list[dict] = []
        for remote_root in _iter_matching_roots(ftp, source):
            try:
                ftp.cwd(remote_root)
                ftp.cwd("/")
            except error_perm:
                continue
            for entry in _iter_remote_files(ftp, remote_root):
                items.append(asdict(entry))
    finally:
        try:
            ftp.quit()
        except Exception:
            pass

    return {"source_key": source.source_key, "host": host, "items": items}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build RAW remote inventory for AstroManager")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--source-key", default=RAW_SOURCE_KEY_DEFAULT)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="anonymous")
    parser.add_argument("--password", default="")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args(argv)

    source = load_device_source(args.db_path, args.source_key)
    payload = build_inventory(source, args.host, args.user, args.password, args.timeout)

    with open(args.output_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"inventory_items={len(payload['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
