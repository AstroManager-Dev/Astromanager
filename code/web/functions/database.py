import sqlite3
from typing import Any
from flask import request
from .common import DB_PATH, DB_TABLE_DEFAULTS


def db_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def db_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def db_table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(r["name"]) for r in rows]


def db_all_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name COLLATE NOCASE ASC
        """
    ).fetchall()
    return [str(r["name"]) for r in rows]


def build_table_config(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    cfg: dict[str, dict[str, Any]] = {}
    for table in db_all_tables(conn):
        columns = db_table_columns(conn, table)
        default_cfg = DB_TABLE_DEFAULTS.get(table, {})
        default_sort = default_cfg.get("default_sort", "id")
        if default_sort not in columns:
            default_sort = "id" if "id" in columns else (columns[0] if columns else "id")
        search_columns = [c for c in default_cfg.get("search_columns", []) if c in columns]
        if not search_columns:
            search_columns = columns[:]
        cfg[table] = {
            "default_sort": default_sort,
            "search_columns": search_columns,
        }
    return cfg


def parse_int_arg(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = request.args.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def parse_text_arg(name: str, default: str = "") -> str:
    return request.args.get(name, default).strip()


def dedupe_runs(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in rows:
        item = dict(row)
        key = (
            str(item.get("job_name", "")),
            str(item.get("started_at", "")),
            str(item.get("status", "")),
        )

        current = grouped.get(key)
        if current is None:
            grouped[key] = item
            continue

        current_source = str(current.get("source", ""))
        new_source = str(item.get("source", ""))

        def source_rank(value: str) -> int:
            if value == "workflow":
                return 3
            if value == "astroctl":
                return 2
            if value == "web":
                return 2
            return 1

        if source_rank(new_source) > source_rank(current_source):
            grouped[key] = item
            continue

        current_note = str(current.get("note", "") or "")
        new_note = str(item.get("note", "") or "")
        if len(new_note) > len(current_note):
            current["note"] = new_note

    deduped = list(grouped.values())
    deduped.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
    return deduped[:20]


def db_recent_runs() -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    conn = db_conn()
    try:
        rows = conn.execute(
            """
            SELECT id, job_name, status, started_at, finished_at, source, note
            FROM job_runs
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()
        return dedupe_runs(rows)
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def db_tables_summary() -> list[dict[str, Any]]:
    conn = db_conn()
    try:
        table_cfg = build_table_config(conn)
        items: list[dict[str, Any]] = []
        for table in table_cfg:
            exists = db_table_exists(conn, table)
            columns = db_table_columns(conn, table) if exists else []
            count = None
            if exists:
                try:
                    count = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                except sqlite3.OperationalError:
                    count = None
            items.append(
                {
                    "name": table,
                    "exists": exists,
                    "columns": columns,
                    "default_sort": table_cfg[table]["default_sort"],
                    "search_columns": table_cfg[table]["search_columns"],
                    "row_count": count,
                }
            )
        return items
    finally:
        conn.close()


def db_list_table(
    conn: sqlite3.Connection,
    table: str,
    limit: int,
    offset: int,
    sort: str,
    order: str,
    q: str,
) -> dict[str, Any]:
    table_cfg = build_table_config(conn)
    if table not in table_cfg:
        raise ValueError("unknown table")
    if not db_table_exists(conn, table):
        raise ValueError("table missing")

    columns = db_table_columns(conn, table)
    if sort not in columns:
        sort = table_cfg[table]["default_sort"]
    order = "DESC" if order.upper() == "DESC" else "ASC"

    where_parts: list[str] = []
    params: list[Any] = []

    if q:
        like_value = f"%{q}%"
        search_columns = [c for c in table_cfg[table]["search_columns"] if c in columns]
        if search_columns:
            where_parts.append(
                "(" + " OR ".join([f"CAST({col} AS TEXT) LIKE ?" for col in search_columns]) + ")"
            )
            params.extend([like_value] * len(search_columns))

    for key, value in request.args.items():
        if not key.startswith("filter_"):
            continue
        col = key.removeprefix("filter_")
        if col not in columns or value.strip() == "":
            continue
        where_parts.append(f"CAST({col} AS TEXT) = ?")
        params.append(value.strip())

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    total = conn.execute(
        f"SELECT COUNT(*) AS n FROM {table} {where_sql}",
        params,
    ).fetchone()["n"]

    rows = conn.execute(
        f"""
        SELECT *
        FROM {table}
        {where_sql}
        ORDER BY {sort} {order}
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    prev_offset = max(0, offset - limit)
    next_offset = offset + limit

    return {
        "table": table,
        "columns": columns,
        "total": total,
        "limit": limit,
        "offset": offset,
        "sort": sort,
        "order": order,
        "q": q,
        "rows": [row_to_dict(r) for r in rows],
        "has_prev": offset > 0,
        "has_next": next_offset < total,
        "prev_offset": prev_offset,
        "next_offset": next_offset,
        "page_current": (offset // limit) + 1 if limit > 0 else 1,
        "page_total": max(1, ((total - 1) // limit) + 1) if total else 1,
    }
