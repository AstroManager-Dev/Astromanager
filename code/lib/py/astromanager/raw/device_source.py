#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

@dataclass(frozen=True)
class DeviceSource:
    id: int
    source_key: str
    vendor: str
    model: str
    family: str
    protocol: str
    root_pattern: str
    notes: str

    @property
    def root_names(self) -> list[str]:
        return [part.strip() for part in self.root_pattern.split("|") if part.strip()]


def load_device_source(db_path: str, source_key: str) -> DeviceSource:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT id, source_key, vendor, model, family, protocol, root_pattern, notes
            FROM device_sources
            WHERE source_key = ? AND is_active = 1
            """,
            (source_key,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise RuntimeError(f"device source not found or inactive: {source_key}")
    return DeviceSource(**dict(row))
