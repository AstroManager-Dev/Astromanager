#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import os
from dataclasses import dataclass

from .constants import (
    RAW_PLAN_DOWNLOAD_NEW,
    RAW_PLAN_REPLACE_CHANGED,
    RAW_PLAN_REPLACE_DEFECTIVE,
    RAW_PLAN_RESTORE_MISSING_LOCAL,
    RAW_PLAN_SKIP_KNOWN_DEFECT,
    RAW_PLAN_SKIP_SAME,
    RAW_REPLACEABLE_BAD_STATUSES,
    RAW_STATUS_OK,
)

@dataclass(frozen=True)
class KnownFile:
    abs_path: str
    rel_path: str
    size_bytes: int
    mtime_epoch: int
    sha256: str
    file_status: str
    is_current: int

@dataclass(frozen=True)
class RemoteMeta:
    remote_path: str
    remote_dir: str
    file_name: str
    size_bytes: int
    mtime_epoch: int
    local_abs_path: str
    rel_path: str


def decide_sync_action(known: KnownFile | None, remote: RemoteMeta) -> tuple[str, str]:
    if known is None:
        return RAW_PLAN_DOWNLOAD_NEW, "db_unknown"

    if not os.path.exists(known.abs_path):
        return RAW_PLAN_RESTORE_MISSING_LOCAL, "local_missing"

    known_size = int(known.size_bytes)
    remote_size = int(remote.size_bytes)
    known_mtime = int(known.mtime_epoch)
    remote_mtime = int(remote.mtime_epoch)

    same_size = known_size == remote_size and remote_size >= 0
    remote_mtime_known = remote_mtime > 0
    same_mtime = remote_mtime_known and known_mtime == remote_mtime

    if same_size and same_mtime:
        if known.file_status in RAW_REPLACEABLE_BAD_STATUSES:
            return RAW_PLAN_SKIP_KNOWN_DEFECT, "known_defect_same_meta"
        return RAW_PLAN_SKIP_SAME, "same_meta"

    if same_size and not remote_mtime_known:
        if known.file_status in RAW_REPLACEABLE_BAD_STATUSES:
            return RAW_PLAN_SKIP_KNOWN_DEFECT, "known_defect_same_size_unknown_mtime"
        if known.file_status == RAW_STATUS_OK:
            return RAW_PLAN_SKIP_SAME, "same_size_unknown_mtime"

    if known.file_status in RAW_REPLACEABLE_BAD_STATUSES:
        return RAW_PLAN_REPLACE_DEFECTIVE, f"replace_{known.file_status}"

    if known.file_status == RAW_STATUS_OK:
        return RAW_PLAN_REPLACE_CHANGED, "changed_meta"

    return RAW_PLAN_REPLACE_CHANGED, f"changed_meta_{known.file_status}"
