from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

RAW_ROOT = Path(os.environ.get("RAW_ROOT", "/raw"))
RUNTIME_ROOT = Path(os.environ.get("RUNTIME_ROOT", "/runtime"))
LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))
CACHE_FILE = RUNTIME_ROOT / "web_progress_cache.json"
RESET_MARKER = RUNTIME_ROOT / "last_factory_reset.ts"

ASTRO_EXTS = {".fit", ".fits", ".fts", ".xisf"}
CACHE_TTL_SECONDS = 120


def _reset_ts() -> int:
    if not RESET_MARKER.exists():
        return 0
    try:
        return int(RESET_MARKER.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _tail_lines(path: Path, limit: int = 60) -> str:
    text = _read_text(path)
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-limit:])


def _step_logs() -> list[Path]:
    steps_dir = LOG_ROOT / "steps"
    if not steps_dir.exists():
        return []

    reset_ts = _reset_ts()
    logs = []
    for p in steps_dir.glob("*.log"):
        if not p.is_file():
            continue
        try:
            if reset_ts and int(p.stat().st_mtime) < reset_ts:
                continue
        except Exception:
            pass
        logs.append(p)

    logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return logs


def _latest_step_log() -> Path | None:
    logs = _step_logs()
    return logs[0] if logs else None


def _parse_progress_from_text(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "files_indexed": None,
        "files_hashed": None,
        "files_reused": None,
        "cal_assets_indexed": None,
        "sessions_indexed": None,
        "last_progress_line": "",
    }

    progress_lines = [line for line in text.splitlines() if "progress:" in line]
    if not progress_lines:
        return result

    line = progress_lines[-1]

    patterns = {
        "files_indexed": r"files_indexed=(\d+)",
        "files_hashed": r"files_hashed=(\d+)",
        "files_reused": r"files_reused=(\d+)",
        "cal_assets_indexed": r"cal_assets_indexed=(\d+)",
        "sessions_indexed": r"sessions_indexed=(\d+)",
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, line)
        if m:
            result[key] = int(m.group(1))

    result["last_progress_line"] = line
    return result


def _count_raw_files() -> int:
    fits_count = 0
    all_count = 0

    if not RAW_ROOT.exists():
        return 0

    for path in RAW_ROOT.rglob("*"):
        if not path.is_file():
            continue
        all_count += 1
        if path.suffix.lower() in ASTRO_EXTS:
            fits_count += 1

    return fits_count if fits_count > 0 else all_count


def _load_cache() -> dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(data: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _get_total_files_cached() -> int:
    now = int(time.time())
    cache = _load_cache()

    cached_ts = int(cache.get("ts", 0) or 0)
    cached_total = int(cache.get("raw_total_files", 0) or 0)

    if cached_total > 0 and (now - cached_ts) <= CACHE_TTL_SECONDS:
        return cached_total

    total = _count_raw_files()
    cache["ts"] = now
    cache["raw_total_files"] = total
    _save_cache(cache)
    return total


def _running_processes() -> list[str]:
    try:
        proc = subprocess.run(
            ["bash", "-lc", r"ps -ef | grep -E 'index\.sh|resolve\.sh|scan_|targets' | grep -v grep || true"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def _find_latest_progress_log() -> tuple[Path | None, dict[str, Any]]:
    logs = _step_logs()
    for log_path in logs[:25]:
        tail = _tail_lines(log_path, limit=200)
        parsed = _parse_progress_from_text(tail)
        if parsed.get("files_indexed") is not None:
            parsed["tail_source"] = str(log_path)
            return log_path, parsed
    return None, {
        "files_indexed": None,
        "files_hashed": None,
        "files_reused": None,
        "cal_assets_indexed": None,
        "sessions_indexed": None,
        "last_progress_line": "",
        "tail_source": "",
    }


def get_live_progress() -> dict[str, Any]:
    latest_log = _latest_step_log()
    latest_log_path = str(latest_log) if latest_log else ""
    latest_tail = _tail_lines(latest_log, limit=80) if latest_log else ""
    running = _running_processes()

    progress_log, parsed = _find_latest_progress_log()
    total_files = _get_total_files_cached()

    files_indexed = int(parsed.get("files_indexed") or 0)
    files_hashed = int(parsed.get("files_hashed") or 0)
    files_reused = int(parsed.get("files_reused") or 0)
    cal_assets_indexed = int(parsed.get("cal_assets_indexed") or 0)
    sessions_indexed = int(parsed.get("sessions_indexed") or 0)

    progress_pct = 0.0
    if total_files > 0:
        progress_pct = round((files_indexed / total_files) * 100.0, 1)
        if progress_pct > 100:
            progress_pct = 100.0

    if not latest_log_path and not running:
        status = "Bereit. Kein aktiver Lauf und keine Fortschrittsdaten seit dem letzten Werksreset."
    elif running:
        status = f"Lauf aktiv: {files_indexed} / {total_files} Dateien ({progress_pct}%)"
    else:
        status = f"Letzter Stand seit Reset: {files_indexed} / {total_files} Dateien ({progress_pct}%)"

    return {
        "ok": True,
        "active": bool(running),
        "status": status,
        "log_path": latest_log_path,
        "progress_source_log": parsed.get("tail_source", ""),
        "progress_pct": progress_pct,
        "files_total": total_files,
        "files_indexed": files_indexed,
        "files_hashed": files_hashed,
        "files_reused": files_reused,
        "cal_assets_indexed": cal_assets_indexed,
        "sessions_indexed": sessions_indexed,
        "last_progress_line": parsed.get("last_progress_line", ""),
        "tail": latest_tail,
        "running_processes": running,
    }
