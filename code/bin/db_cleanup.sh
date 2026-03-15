#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
# shellcheck source=/dev/null
source "$ROOT/lib/pipeline_env.sh"
# shellcheck source=/dev/null
source "$ROOT/lib/db.sh"

MODE="${1:-index-only}"
SOURCE_KEY="${2:-dwarflab_dwarf3}"

db_init "$ROOT"
SOURCE_ID="$(db_get_source_id "$SOURCE_KEY")"
if [[ -z "${SOURCE_ID:-}" ]]; then
  echo "db_cleanup: unknown source_key=$SOURCE_KEY" >&2
  exit 21
fi

case "$MODE" in
  index-only)
    sqlite3 "$DB_PATH" <<SQL
DELETE FROM sessions WHERE source_id=${SOURCE_ID};
DELETE FROM raw_files WHERE source_id=${SOURCE_ID};
DELETE FROM calibration_assets WHERE source_id=${SOURCE_ID};
SQL
    echo "db_cleanup: removed indexed data for source_key=${SOURCE_KEY} source_id=${SOURCE_ID}"
    ;;
  stale-running)
    sqlite3 "$DB_PATH" "
      UPDATE job_runs
         SET status='aborted',
             finished_at=datetime('now'),
             note=coalesce(note,'') || ' | cleaned stale running entry'
       WHERE status='running';
    "
    echo "db_cleanup: marked stale running job_runs as aborted"
    ;;
  all-runs)
    sqlite3 "$DB_PATH" "DELETE FROM job_runs;"
    echo "db_cleanup: removed all job_runs"
    ;;
  all)
    sqlite3 "$DB_PATH" <<SQL
DELETE FROM sessions WHERE source_id=${SOURCE_ID};
DELETE FROM raw_files WHERE source_id=${SOURCE_ID};
DELETE FROM calibration_assets WHERE source_id=${SOURCE_ID};
DELETE FROM job_runs;
DELETE FROM app_state;
SQL
    echo "db_cleanup: removed source data, job_runs and app_state for source_key=${SOURCE_KEY}"
    ;;
  *)
    echo "usage: db_cleanup.sh [index-only|stale-running|all-runs|all] [source_key]" >&2
    exit 2
    ;;
esac
