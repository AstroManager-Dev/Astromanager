import os
from pathlib import Path

LOG_ROOT = Path(os.environ.get("LOG_ROOT", "/logs"))
LOG_FILE = LOG_ROOT / "master" / "webui.log"
DB_PATH = Path(os.environ.get("DB_PATH", "/runtime/pipeline.db"))
ASTROCTL = "/app/bin/astroctl"
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/app"))
CORE_BACKUP_ROOT = Path(os.environ.get("CORE_BACKUP_ROOT", "/runtime/backups/core"))
SQL_DUMP_ROOT = Path(os.environ.get("SQL_DUMP_ROOT", "/runtime/backups/sql"))
UPLOAD_ROOT = Path(os.environ.get("UPLOAD_ROOT", "/runtime/uploads"))
PROJECT_CORE_ROOT = Path(os.environ.get("PROJECT_CORE_ROOT", "/project-core"))

DB_TABLE_DEFAULTS = {
    "sessions": {
        "default_sort": "id",
        "search_columns": ["raw_session_path", "target", "category", "status", "filter_set", "session_type"],
    },
    "targets": {
        "default_sort": "id",
        "search_columns": ["canonical_name", "display_name", "category", "final_name"],
    },
    "capture_profiles": {
        "default_sort": "id",
        "search_columns": ["camera", "filter_set"],
    },
    "calibration_assets": {
        "default_sort": "id",
        "search_columns": ["asset_type", "asset_origin", "camera", "abs_path", "rel_path"],
    },
    "raw_files": {
        "default_sort": "id",
        "search_columns": [
            "file_name", "abs_path", "rel_path", "source_domain", "source_subtype",
            "filter_set", "file_status", "derivative_kind", "header_object",
            "header_bayerpat", "header_date_obs",
        ],
    },
}

TARGET_THUMBNAIL_FILE_NAME = "stacked_thumbnail.jpg"
TARGET_THUMB_CENTER_RADIUS_FACTOR = 0.05
