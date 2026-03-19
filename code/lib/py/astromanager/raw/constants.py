#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
RAW_SOURCE_KEY_DEFAULT = "dwarflab_dwarf3"
RAW_REMOTE_BASE_DIR = "/Astronomy"
RAW_FITS_EXTENSIONS = (".fits", ".fit", ".fts")
RAW_DEFAULT_ALLOWED_EXTENSIONS = RAW_FITS_EXTENSIONS
RAW_PLAN_DOWNLOAD_NEW = "download_new"
RAW_PLAN_SKIP_SAME = "skip_same"
RAW_PLAN_RESTORE_MISSING_LOCAL = "restore_missing_local"
RAW_PLAN_REPLACE_CHANGED = "replace_changed"
RAW_PLAN_REPLACE_DEFECTIVE = "replace_defective"
RAW_PLAN_SKIP_KNOWN_DEFECT = "skip_known_defect"
RAW_STATUS_OK = "ok"
RAW_STATUS_BADFIT = "badfit"
RAW_STATUS_DEFECT = "defect"
RAW_REPLACEABLE_BAD_STATUSES = {RAW_STATUS_BADFIT, RAW_STATUS_DEFECT}
RAW_RUNTIME_SUBDIR = "raw_sync"
