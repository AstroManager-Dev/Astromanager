from __future__ import annotations

from .common import ASTROCTL, build_response, insert_job_run, start_background


def handle() -> dict:
    cmd = f"{ASTROCTL} index sessions"
    res = start_background(cmd, "index_sessions")

    insert_job_run(
        job_name="workflow_index",
        status="started",
        source="web",
        note=cmd,
    )

    return build_response(
        action="index_sessions",
        ok=True,
        stdout=res["stdout"],
        stderr="",
        returncode=0,
        details={
            "started": True,
            "pid": res["pid"],
            "log_path": res["log_path"],
            "cmd": cmd,
            "message": "Index Sessions im Hintergrund gestartet. Targets laufen ueber den 9999-Step mit.",
        },
    )
