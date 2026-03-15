#!/usr/bin/env python3
import sys

from astromanager.paths import TARGET_RESOLVER_TABLE_SYNC_MODULE
from astromanager.targets.resolver_table_sync import sync_mode


def main(argv=None):
    argv = argv or sys.argv[1:]
    db_path = argv[0] if len(argv) > 0 else "/runtime/pipeline.db"
    mode = argv[1] if len(argv) > 1 else ""

    print(f"target_resolver_table_sync_module={TARGET_RESOLVER_TABLE_SYNC_MODULE}")
    sync_mode(db_path, mode)


if __name__ == "__main__":
    main()
