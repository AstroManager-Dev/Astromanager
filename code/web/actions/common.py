from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

DB_PATH = Path(os.environ.get("DB_PATH", "/runtime/pipeline.db"))
LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))


def run_shell(cmd: str, timeout: int = 3600) -> dict[str, Any]:
    proc = subprocess.run(
        ["bash", "-lc", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "cmd": cmd,
    }


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_job_run(job_name: str, status: str, source: str, note: str = "") -> int | None:
    if not DB_PATH.exists():
        return None

    conn = db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO job_runs (job_name, status, started_at, finished_at, source, note)
            VALUES (?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'), ?, ?)
            """,
            (job_name, status, source, note),
        )
        conn.commit()
        return int(cur.lastrowid)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def build_response(
    action: str,
    ok: bool,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": ok,
        "action": action,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }
    if details:
        payload["details"] = details
    return payload
