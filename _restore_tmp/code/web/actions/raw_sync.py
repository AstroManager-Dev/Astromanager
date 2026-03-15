from __future__ import annotations

from .common import ASTROCTL, build_response, start_background


def handle() -> dict:
    cmd = f"{ASTROCTL} raw sync"
    res = start_background(cmd, "raw_sync")
    return build_response(
        action="raw_sync",
        ok=True,
        stdout=res["stdout"],
        stderr="",
        returncode=0,
        details={
            "started": True,
            "pid": res["pid"],
            "log_path": res["log_path"],
            "cmd": cmd,
            "message": "RAW Sync im Hintergrund gestartet.",
        },
    )
