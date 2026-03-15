from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from .common import build_response, run_shell, start_background

CORE_BACKUP_ROOT = Path(os.environ.get("CORE_BACKUP_ROOT", "/runtime/backups/core"))
CORE_BACKUP_SCRIPT = Path("/app/bin/core_backup_zip.sh")
CORE_RESTORE_SCRIPT = Path("/app/bin/core_restore_zip.sh")
SQL_DUMP_SCRIPT = Path("/app/bin/core_sql_dump_zip.sh")
SQL_DUMP_ROOT = Path(os.environ.get("SQL_DUMP_ROOT", "/runtime/backups/sql"))


def _latest_backup() -> Path | None:
    if not CORE_BACKUP_ROOT.exists():
        return None
    zips = sorted(CORE_BACKUP_ROOT.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


def backup_handle() -> dict:
    if not CORE_BACKUP_SCRIPT.exists():
        return build_response("backup_create", False, "", f"Missing script: {CORE_BACKUP_SCRIPT}\n", 1)
    cmd = f"{CORE_BACKUP_SCRIPT} webui"
    res = start_background(cmd, "backup_create")
    return build_response(
        action="backup_create",
        ok=True,
        stdout=res["stdout"],
        stderr="",
        returncode=0,
        details={
            "started": True,
            "pid": res["pid"],
            "log_path": res["log_path"],
            "cmd": cmd,
            "message": "Core-Backup gestartet.",
        },
    )


def restore_latest_backup_handle() -> dict:
    latest = _latest_backup()
    if latest is None:
        return build_response("backup_restore_latest", False, "", "Kein Core-Backup gefunden.\n", 1)
    cmd = f"{CORE_RESTORE_SCRIPT} '{latest}'"
    res = run_shell(cmd, timeout=900)
    return build_response(
        action="backup_restore_latest",
        ok=res["ok"],
        stdout=res["stdout"],
        stderr=res["stderr"],
        returncode=res["returncode"],
        details={
            "zip_path": str(latest),
            "cmd": cmd,
            "message": "Letztes Core-Backup zurückgespielt." if res["ok"] else "Restore fehlgeschlagen.",
        },
    )


def sql_dump_handle() -> dict:
    SQL_DUMP_ROOT.mkdir(parents=True, exist_ok=True)
    dump_path = SQL_DUMP_ROOT / f"pipeline_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"
    cmd = f"sqlite3 /runtime/pipeline.db .dump > '{dump_path}'"
    res = run_shell(cmd, timeout=300)
    return build_response(
        action="sql_dump",
        ok=res["ok"],
        stdout=(res["stdout"] or "") + (f"SQL-Dump erstellt: {dump_path}\n" if res["ok"] else ""),
        stderr=res["stderr"],
        returncode=res["returncode"],
        details={
            "dump_path": str(dump_path),
            "cmd": cmd,
            "message": "SQL-Dump erstellt." if res["ok"] else "SQL-Dump fehlgeschlagen.",
        },
    )
