from pathlib import Path
import re
from typing import Any

from progress_runtime import get_live_progress

from .common import CORE_BACKUP_ROOT, LOG_FILE, SQL_DUMP_ROOT, UPLOAD_ROOT
from .database import db_recent_runs


def latest_web_log(limit: int = 40) -> str:
    if not LOG_FILE.exists():
        return ""
    try:
        return "".join(LOG_FILE.read_text(encoding="utf-8").splitlines(keepends=True)[-limit:])
    except Exception:
        return ""


def running_jobs() -> list[dict[str, Any]]:
    return [run for run in db_recent_runs() if str(run.get("status", "")).lower() in {"running", "started"}]


def _note_metric(text: str, key: str) -> int | None:
    match = re.search(rf"(?:^|[,\s]){re.escape(key)}=([^,\s]+)", text or "")
    if not match:
        return None
    try:
        return int(str(match.group(1)).strip())
    except ValueError:
        return None


def featured_metrics(progress: dict[str, Any], run: dict[str, Any] | None) -> dict[str, int | None]:
    note = str((run or {}).get("note") or "")

    def progress_int(key: str) -> int | None:
        value = progress.get(key)
        return value if isinstance(value, int) else None

    return {
        "skipped": progress_int("skipped") if progress.get("active") else _note_metric(note, "sessions_skipped_unchanged"),
        "indexed": progress_int("files_indexed") if progress.get("active") else _note_metric(note, "files_indexed"),
        "hashes": progress_int("files_hashed") if progress.get("active") else _note_metric(note, "files_hashed"),
        "reused": progress_int("files_reused") if progress.get("active") else _note_metric(note, "files_reused"),
    }


def summarize_service_state() -> dict[str, Any]:
    progress = get_live_progress()
    active_runs = running_jobs()
    current_job = active_runs[0] if active_runs else None
    title = "Bereit"
    subtitle = "Kein aktiver Job"
    if progress.get("active"):
        title = "Lauf aktiv"
        subtitle = progress.get("status") or "AstroManager arbeitet"
    elif current_job:
        title = current_job.get("job_name") or "Letzter Job"
        subtitle = current_job.get("status") or "running"
    elif progress.get("status"):
        subtitle = progress.get("status")

    recent_runs = db_recent_runs()
    featured_run = current_job or (recent_runs[0] if recent_runs else None)

    return {
        "title": title,
        "subtitle": subtitle,
        "active": bool(progress.get("active")),
        "workflow": progress.get("workflow") or "idle",
        "current_step": progress.get("current_step") or "",
        "progress_pct": progress.get("progress_pct") or 0,
        "current_job": current_job,
        "featured_run": featured_run,
        "featured_metrics": featured_metrics(progress, featured_run),
        "active_runs": active_runs,
        "recent_runs": recent_runs,
        "latest_log": latest_web_log(),
    }


def file_cards_from_dir(path: Path, label: str, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for fp in sorted([p for p in path.glob('*') if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        stat = fp.stat()
        items.append({
            "name": fp.name,
            "label": label,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        })
    return items


def fmt_size(num: int) -> str:
    value = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num} B"


def dev_assets() -> dict[str, list[dict[str, Any]]]:
    backups = file_cards_from_dir(CORE_BACKUP_ROOT, "Core Backup", limit=50)
    sql_dumps = file_cards_from_dir(SQL_DUMP_ROOT, "SQL", limit=50)
    for bucket in (backups, sql_dumps):
        for item in bucket:
            item["size_label"] = fmt_size(int(item["size"]))
    latest_backup = backups[0] if backups else None
    return {"backups": backups, "sql_dumps": sql_dumps, "latest_backup": latest_backup}


def resolve_download(bucket: str, filename: str) -> Path:
    roots = {"backup": CORE_BACKUP_ROOT, "sql": SQL_DUMP_ROOT}
    if bucket not in roots:
        raise FileNotFoundError(bucket)
    safe_name = Path(filename).name
    target = (roots[bucket] / safe_name).resolve()
    root = roots[bucket].resolve()
    if root not in target.parents and target != root:
        raise FileNotFoundError(filename)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(filename)
    return target


def append_web_log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")
