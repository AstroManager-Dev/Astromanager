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


def _tail_lines(path: Path, limit: int = 120) -> str:
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
    logs: list[Path] = []

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


def _detect_workflow(log_path: Path | None) -> str:
    if not log_path:
        return "idle"

    name = log_path.name.lower()
    if "raw_sync" in name:
        return "raw_sync"
    if name.startswith("index_"):
        return "index"
    if "target" in name or "resolve" in name:
        return "targets"
    if "masterdark" in name:
        return "masterdarks"
    if "siril" in name:
        return "siril"
    return "generic"


def _extract_current_step(text: str) -> str:
    matches = re.findall(r"run step(?::|=)\s*([^\n]+)", text)
    if matches:
        return matches[-1].strip()
    return ""


def _parse_index_metrics(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "files_indexed": 0,
        "files_hashed": 0,
        "files_reused": 0,
        "cal_assets_indexed": 0,
        "sessions_indexed": 0,
        "sessions_skipped_unchanged": 0,
        "last_progress_line": "",
    }

    summary_match = None
    for line in text.splitlines():
        if "workflow=" in line and "files_indexed=" in line:
            summary_match = line

    if summary_match:
        line = summary_match
        patterns = {
            "files_indexed": r"files_indexed=(\d+)",
            "files_hashed": r"files_hashed=(\d+)",
            "files_reused": r"files_reused=(\d+)",
            "cal_assets_indexed": r"cal_assets_indexed=(\d+)",
            "sessions_indexed": r"sessions_indexed=(\d+)",
            "sessions_skipped_unchanged": r"sessions_skipped_unchanged=(\d+)",
        }
        for key, pattern in patterns.items():
            m = re.search(pattern, line)
            if m:
                result[key] = int(m.group(1))
        result["last_progress_line"] = line
        return result

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


def _parse_raw_sync_summary(text: str) -> dict[str, Any]:
    result = {
        "plan_count": 0,
        "downloaded": 0,
        "skipped": 0,
        "errors": 0,
        "plan_counters": {},
        "result_counters": {},
        "summary_line": "",
    }

    for line in reversed(text.splitlines()):
        if "raw sync summary:" not in line:
            continue
        payload = line.split("raw sync summary:", 1)[1].strip()
        try:
            data = json.loads(payload)
        except Exception:
            continue

        result["plan_count"] = int(data.get("plan_count") or 0)
        result["plan_counters"] = data.get("plan_counters") or {}
        counters = data.get("result_counters") or {}
        result["result_counters"] = counters
        result["downloaded"] = int(counters.get("downloaded") or 0)
        result["skipped"] = int(counters.get("skipped") or 0)
        result["errors"] = int(counters.get("errors") or 0)
        result["summary_line"] = line
        return result

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
            [
                "bash",
                "-lc",
                r"ps -ef | grep -E '/app/bin/astroctl raw sync|/app/bin/astroctl index sessions|workflows/raw/sync\.sh|workflows/index/index\.sh|workflows/targets/resolve\.sh|masterdarks|siril' | grep -v grep || true",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def get_live_progress() -> dict[str, Any]:
    latest_log = _latest_step_log()
    workflow = _detect_workflow(latest_log)
    latest_log_path = str(latest_log) if latest_log else ""
    tail = _tail_lines(latest_log, limit=200) if latest_log else ""
    running = _running_processes()
    current_step = _extract_current_step(tail)
    total_files = _get_total_files_cached()

    payload: dict[str, Any] = {
        "ok": True,
        "active": bool(running),
        "workflow": workflow,
        "status": "Bereit.",
        "current_step": current_step,
        "log_path": latest_log_path,
        "progress_pct": 0.0,
        "files_total": total_files,
        "files_indexed": 0,
        "files_hashed": 0,
        "files_reused": 0,
        "cal_assets_indexed": 0,
        "sessions_indexed": 0,
        "sessions_skipped_unchanged": 0,
        "plan_count": 0,
        "downloaded": 0,
        "skipped": 0,
        "errors": 0,
        "last_progress_line": "",
        "tail": tail,
        "running_processes": running,
    }

    if not latest_log:
        if running:
            payload["status"] = "Lauf aktiv, aber noch kein Step-Log gefunden."
        else:
            payload["status"] = "Bereit. Kein aktiver Lauf und keine Fortschrittsdaten seit dem letzten Werksreset."
        return payload

    if workflow == "raw_sync":
        raw = _parse_raw_sync_summary(tail)
        plan_count = int(raw["plan_count"] or 0)
        downloaded = int(raw["downloaded"] or 0)
        skipped = int(raw["skipped"] or 0)
        errors = int(raw["errors"] or 0)
        done = downloaded + skipped + errors

        pct = 0.0
        if plan_count > 0:
            pct = round((done / plan_count) * 100.0, 1)
            if pct > 100:
                pct = 100.0

        payload.update(
            {
                "progress_pct": pct,
                "plan_count": plan_count,
                "downloaded": downloaded,
                "skipped": skipped,
                "errors": errors,
                "last_progress_line": raw.get("summary_line", ""),
            }
        )

        if running:
            payload["status"] = f"RAW Sync aktiv: {current_step or 'laufend'}"
        elif plan_count > 0:
            payload["status"] = f"Letzter RAW Sync: {done} / {plan_count} Dateien ({pct}%)"
        else:
            payload["status"] = "Letzter RAW Sync ohne auswertbare Summary."
        return payload

    index = _parse_index_metrics(tail)
    files_indexed = int(index.get("files_indexed") or 0)
    files_hashed = int(index.get("files_hashed") or 0)
    files_reused = int(index.get("files_reused") or 0)
    cal_assets_indexed = int(index.get("cal_assets_indexed") or 0)
    sessions_indexed = int(index.get("sessions_indexed") or 0)
    sessions_skipped_unchanged = int(index.get("sessions_skipped_unchanged") or 0)

    pct = 0.0
    if total_files > 0:
        pct = round((files_indexed / total_files) * 100.0, 1)
        if pct > 100:
            pct = 100.0

    payload.update(
        {
            "progress_pct": pct,
            "files_indexed": files_indexed,
            "files_hashed": files_hashed,
            "files_reused": files_reused,
            "cal_assets_indexed": cal_assets_indexed,
            "sessions_indexed": sessions_indexed,
            "sessions_skipped_unchanged": sessions_skipped_unchanged,
            "last_progress_line": index.get("last_progress_line", ""),
        }
    )

    if running:
        payload["status"] = f"Lauf aktiv: {current_step or workflow}"
    else:
        payload["status"] = f"Letzter Stand seit Reset: {files_indexed} / {total_files} Dateien ({pct}%)"

    return payload
