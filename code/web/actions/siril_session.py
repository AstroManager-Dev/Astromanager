from __future__ import annotations

from .common import build_response, insert_job_run


def handle() -> dict:
    insert_job_run(
        job_name="siril_session_dummy",
        status="ok",
        source="web",
        note="Dummy-Handler aktiv",
    )
    return build_response(
        action="siril_session",
        ok=True,
        stdout="Siril Session Dummy-Handler aktiv. Umsetzung folgt.\n",
        stderr="",
        returncode=0,
        details={"dummy": True},
    )
