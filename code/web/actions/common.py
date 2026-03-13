from __future__ import annotations

import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(os.environ.get("DB_PATH", "/runtime/pipeline.db"))
LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))
WEB_ACTION_LOG_ROOT = LOG_ROOT / "web_actions"
ASTROCTL = os.environ.get("ASTROCTL", "/app/bin/astroctl")


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


def start_background(cmd: str, log_prefix: str) -> dict[str, Any]:
    WEB_ACTION_LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = WEB_ACTION_LOG_ROOT / f"{log_prefix}_{stamp}.log"
    handle = log_path.open("a", encoding="utf-8")
    handle.write(f"[web] start cmd={cmd}\n")
    handle.flush()

    proc = subprocess.Popen(
        ["bash", "-lc", cmd],
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    handle.close()

    return {
        "ok": True,
        "returncode": 0,
        "stdout": f"Gestartet: {cmd}\nPID: {proc.pid}\nLog: {log_path}\n",
        "stderr": "",
        "cmd": cmd,
        "pid": proc.pid,
        "log_path": str(log_path),
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
