from __future__ import annotations

from .common import build_response, insert_job_run, run_shell


def handle() -> dict:
    steps = []

    cmd_index = "cd /app/workflows/index && ./index.sh"
    res_index = run_shell(cmd_index, timeout=7200)
    steps.append({
        "step": "index",
        "ok": res_index["ok"],
        "returncode": res_index["returncode"],
        "cmd": res_index["cmd"],
        "stdout": res_index["stdout"],
        "stderr": res_index["stderr"],
    })
    insert_job_run(
        job_name="workflow_index",
        status="ok" if res_index["ok"] else "error",
        source="web",
        note=cmd_index,
    )

    if not res_index["ok"]:
        return build_response(
            action="index_sessions",
            ok=False,
            stdout=res_index["stdout"],
            stderr=res_index["stderr"],
            returncode=res_index["returncode"],
            details={"steps": steps, "message": "Workflow index fehlgeschlagen."},
        )

    cmd_targets = "cd /app/workflows/targets && ./resolve.sh"
    res_targets = run_shell(cmd_targets, timeout=7200)
    steps.append({
        "step": "targets",
        "ok": res_targets["ok"],
        "returncode": res_targets["returncode"],
        "cmd": res_targets["cmd"],
        "stdout": res_targets["stdout"],
        "stderr": res_targets["stderr"],
    })
    insert_job_run(
        job_name="workflow_targets",
        status="ok" if res_targets["ok"] else "error",
        source="web",
        note=cmd_targets,
    )

    ok = res_index["ok"] and res_targets["ok"]
    combined_stdout = (
        "=== STEP: index ===\n"
        + (res_index["stdout"] or "")
        + "\n\n=== STEP: targets ===\n"
        + (res_targets["stdout"] or "")
    ).strip()
    combined_stderr = (
        "=== STEP: index ===\n"
        + (res_index["stderr"] or "")
        + "\n\n=== STEP: targets ===\n"
        + (res_targets["stderr"] or "")
    ).strip()

    return build_response(
        action="index_sessions",
        ok=ok,
        stdout=combined_stdout,
        stderr=combined_stderr,
        returncode=0 if ok else 1,
        details={
            "steps": steps,
            "message": "Index + Targets abgeschlossen." if ok else "Index oder Targets fehlgeschlagen.",
        },
    )
