from __future__ import annotations

from .common import ASTROCTL, build_response, insert_job_run, start_background


def handle() -> dict:
    cmd = f"{ASTROCTL} raw sync"
    res = start_background(cmd, "raw_sync")

    insert_job_run(
        job_name="workflow_raw_sync",
        status="started",
        source="web",
        note=cmd,
    )

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
