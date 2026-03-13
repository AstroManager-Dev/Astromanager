from __future__ import annotations

import os
from pathlib import Path

from .common import ASTROCTL, build_response, run_shell, start_background

PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '/app'))
BACKUP_SCRIPT = Path(os.environ.get('BACKUP_SCRIPT', str(PROJECT_ROOT / 'backup_astromanager_nomedia_zip.sh')))
SQL_DUMP_ROOT = Path(os.environ.get('SQL_DUMP_ROOT', str(PROJECT_ROOT / '_backups' / 'astromanager' / 'sql_dumps')))


def backup_handle() -> dict:
    if not BACKUP_SCRIPT.exists():
        return build_response(
            action='backup_create',
            ok=False,
            stdout='',
            stderr=f'Backup-Skript nicht gefunden: {BACKUP_SCRIPT}\n',
            returncode=1,
        )

    cmd = f"{BACKUP_SCRIPT} --label webui"
    res = start_background(cmd, 'backup_create')
    return build_response(
        action='backup_create',
        ok=True,
        stdout=res['stdout'],
        stderr='',
        returncode=0,
        details={
            'started': True,
            'pid': res['pid'],
            'log_path': res['log_path'],
            'cmd': cmd,
            'message': 'Backup-Erstellung im Hintergrund gestartet.',
        },
    )


def sql_dump_handle() -> dict:
    SQL_DUMP_ROOT.mkdir(parents=True, exist_ok=True)
    dump_path = SQL_DUMP_ROOT / f"pipeline_{__import__('datetime').datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"
    cmd = f"sqlite3 /runtime/pipeline.db .dump > '{dump_path}'"
    res = run_shell(cmd, timeout=300)
    return build_response(
        action='sql_dump',
        ok=res['ok'],
        stdout=(res['stdout'] or '') + (f"SQL-Dump erstellt: {dump_path}\n" if res['ok'] else ''),
        stderr=res['stderr'],
        returncode=res['returncode'],
        details={
            'dump_path': str(dump_path),
            'cmd': cmd,
            'message': 'SQL-Dump erstellt.' if res['ok'] else 'SQL-Dump fehlgeschlagen.',
        },
    )


def organizer_refresh_handle() -> dict:
    cmd = f"{ASTROCTL} db init"
    res = run_shell(cmd, timeout=300)
    return build_response(
        action='organizer_refresh',
        ok=res['ok'],
        stdout=(res['stdout'] or '') + ('Programm-Daten-Organizer aktualisiert.\n' if res['ok'] else ''),
        stderr=res['stderr'],
        returncode=res['returncode'],
        details={
            'cmd': cmd,
            'message': 'DB-Initialisierung und Strukturabgleich ausgeführt.' if res['ok'] else 'Organizer-Aktualisierung fehlgeschlagen.',
        },
    )
