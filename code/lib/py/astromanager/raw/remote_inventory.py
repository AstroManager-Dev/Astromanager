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
import socket
from dataclasses import asdict, dataclass
from ftplib import FTP, error_perm
from typing import Iterator

from .constants import RAW_SOURCE_KEY_DEFAULT
from .device_instance import DeviceInstance, load_device_instance


class RawFtpError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RemoteFile:
    remote_path: str
    remote_dir: str
    file_name: str
    size_bytes: int
    mtime_epoch: int


def _connect(host: str, port: int, user: str, password: str, timeout: int) -> FTP:
    ftp = FTP()
    try:
        ftp.connect(host=host, port=port, timeout=timeout)
    except socket.gaierror as exc:
        raise RawFtpError("ftp_host_unreachable", f"ftp host unreachable host={host}: {exc}") from exc
    except ConnectionRefusedError as exc:
        raise RawFtpError("ftp_port_closed", f"ftp port {port} closed host={host}: {exc}") from exc
    except TimeoutError as exc:
        raise RawFtpError("ftp_timeout", f"ftp timeout host={host} timeout={timeout}: {exc}") from exc
    except socket.timeout as exc:
        raise RawFtpError("ftp_timeout", f"ftp timeout host={host} timeout={timeout}: {exc}") from exc
    except OSError as exc:
        msg = str(exc).lower()
        if "no route to host" in msg or "network is unreachable" in msg or "name or service not known" in msg:
            raise RawFtpError("ftp_host_unreachable", f"ftp host unreachable host={host}: {exc}") from exc
        if "connection refused" in msg:
            raise RawFtpError("ftp_port_closed", f"ftp port {port} closed host={host}: {exc}") from exc
        if "timed out" in msg:
            raise RawFtpError("ftp_timeout", f"ftp timeout host={host} timeout={timeout}: {exc}") from exc
        raise RawFtpError("ftp_connect_failed", f"ftp connect failed host={host}: {exc}") from exc

    try:
        ftp.login(user=user, passwd=password)
    except error_perm as exc:
        raise RawFtpError("ftp_login_failed", f"ftp login failed host={host} user={user}: {exc}") from exc
    except TimeoutError as exc:
        raise RawFtpError("ftp_timeout", f"ftp timeout during login host={host} timeout={timeout}: {exc}") from exc
    except socket.timeout as exc:
        raise RawFtpError("ftp_timeout", f"ftp timeout during login host={host} timeout={timeout}: {exc}") from exc
    except OSError as exc:
        msg = str(exc).lower()
        if "timed out" in msg:
            raise RawFtpError("ftp_timeout", f"ftp timeout during login host={host} timeout={timeout}: {exc}") from exc
        raise RawFtpError("ftp_login_failed", f"ftp login failed host={host} user={user}: {exc}") from exc

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


def _iter_remote_files(ftp: FTP, base_dir: str, allowed_extensions: tuple[str, ...]) -> Iterator[RemoteFile]:
    for name, facts in _list_dir_entries(ftp, base_dir):
        child = facts.get("path") or posixpath.join(base_dir, name)
        kind = (facts.get("type") or "").lower()

        if kind == "dir":
            yield from _iter_remote_files(ftp, child, allowed_extensions)
            continue

        if kind not in ("", "file"):
            continue

        file_name = posixpath.basename(child)
        if not file_name.lower().endswith(allowed_extensions):
            continue

        yield RemoteFile(
            remote_path=child,
            remote_dir=posixpath.dirname(child),
            file_name=file_name,
            size_bytes=int(facts.get("size") or -1),
            mtime_epoch=_mtime_from_modify(facts.get("modify") or ""),
        )


def _iter_matching_roots(ftp: FTP, instance: DeviceInstance) -> Iterator[str]:
    patterns = instance.root_names
    for name, facts in _list_dir_entries(ftp, instance.remote_base_dir):
        kind = (facts.get("type") or "").lower()
        if kind != "dir":
            continue
        dir_name = name or posixpath.basename(facts.get("path") or "")
        if not dir_name:
            continue
        if any(fnmatch.fnmatchcase(dir_name, pattern) for pattern in patterns):
            yield facts.get("path") or posixpath.join(instance.remote_base_dir, dir_name)


def build_inventory(instance: DeviceInstance) -> dict:
    if instance.protocol.lower() != "ftp":
        raise RuntimeError(f"unsupported protocol for initial RAW sync: {instance.protocol}")

    ftp = _connect(instance.host, instance.port, instance.username, instance.password_text, instance.timeout_seconds)
    try:
        items: list[dict] = []
        for remote_root in _iter_matching_roots(ftp, instance):
            try:
                ftp.cwd(remote_root)
                ftp.cwd("/")
            except error_perm:
                continue
            for entry in _iter_remote_files(ftp, remote_root, instance.allowed_extensions):
                items.append(asdict(entry))
    finally:
        try:
            ftp.quit()
        except Exception:
            pass

    return {
        "instance_key": instance.instance_key,
        "source_key": instance.source_key,
        "host": instance.host,
        "items": items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build RAW remote inventory for AstroManager")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--instance-key", required=True)
    parser.add_argument("--source-key", default=RAW_SOURCE_KEY_DEFAULT)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args(argv)

    try:
        instance = load_device_instance(args.db_path, args.instance_key)
        payload = build_inventory(instance)
    except RawFtpError as exc:
        print(f"raw_sync_error_code={exc.code}")
        print(f"raw_sync_error_message={exc.message}")
        raise SystemExit(20) from exc

    with open(args.output_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"inventory_items={len(payload['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
