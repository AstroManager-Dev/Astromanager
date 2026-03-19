#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .constants import RAW_FITS_EXTENSIONS, RAW_REMOTE_BASE_DIR


def _parse_extensions(value: str) -> tuple[str, ...]:
    items = [part.strip().lower() for part in (value or "").split(",") if part.strip()]
    return tuple(items) if items else RAW_FITS_EXTENSIONS


@dataclass(frozen=True)
class DeviceInstance:
    id: int
    instance_key: str
    display_name: str
    source_id: int
    source_key: str
    vendor: str
    model: str
    family: str
    protocol: str
    root_pattern: str
    connection_kind: str
    host: str
    port: int
    auth_mode: str
    username: str
    password_text: str
    timeout_seconds: int
    remote_base_dir: str
    allowed_extensions_csv: str
    notes: str
    is_active: int
    is_default: int

    @property
    def root_names(self) -> list[str]:
        return [part.strip() for part in self.root_pattern.split("|") if part.strip()]

    @property
    def allowed_extensions(self) -> tuple[str, ...]:
        return _parse_extensions(self.allowed_extensions_csv)


_SELECT_SQL = """
SELECT
  di.id,
  di.instance_key,
  di.display_name,
  di.source_id,
  ds.source_key,
  ds.vendor,
  ds.model,
  ds.family,
  ds.protocol,
  ds.root_pattern,
  di.connection_kind,
  di.host,
  di.port,
  di.auth_mode,
  di.username,
  di.password_text,
  di.timeout_seconds,
  COALESCE(NULLIF(di.remote_base_dir_override, ''), NULLIF(ds.remote_base_dir, ''), ?) AS remote_base_dir,
  COALESCE(NULLIF(di.allowed_extensions_override, ''), NULLIF(ds.allowed_extensions, ''), ?) AS allowed_extensions_csv,
  COALESCE(di.notes, '') AS notes,
  di.is_active,
  di.is_default
FROM device_instances di
JOIN device_sources ds ON ds.id = di.source_id
WHERE di.is_active = 1
"""


def _row_to_instance(row: sqlite3.Row | None) -> DeviceInstance:
    if row is None:
        raise RuntimeError("device instance not found or inactive")
    payload = dict(row)
    payload["port"] = int(payload.get("port") or 21)
    payload["timeout_seconds"] = int(payload.get("timeout_seconds") or 15)
    payload["is_active"] = int(payload.get("is_active") or 0)
    payload["is_default"] = int(payload.get("is_default") or 0)
    return DeviceInstance(**payload)


def load_device_instance(db_path: str, instance_key: str) -> DeviceInstance:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            _SELECT_SQL + " AND di.instance_key = ? ORDER BY di.is_default DESC, di.id LIMIT 1",
            (RAW_REMOTE_BASE_DIR, ",".join(RAW_FITS_EXTENSIONS), instance_key),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise RuntimeError(f"device instance not found or inactive: {instance_key}")
    return _row_to_instance(row)


def list_active_device_instances(db_path: str, source_key: str = "") -> list[DeviceInstance]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = _SELECT_SQL
        params: list[str] = [RAW_REMOTE_BASE_DIR, ",".join(RAW_FITS_EXTENSIONS)]
        if source_key:
            sql += " AND ds.source_key = ?"
            params.append(source_key)
        sql += " ORDER BY di.is_default DESC, di.id"
        rows = conn.execute(sql, tuple(params)).fetchall()
    finally:
        conn.close()
    return [_row_to_instance(row) for row in rows]
