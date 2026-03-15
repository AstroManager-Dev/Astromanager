#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
import os
import sys
APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY = os.path.join(APP_ROOT, "lib", "py")
if LIB_PY not in sys.path:
    sys.path.insert(0, LIB_PY)
from astromanager.raw.fetch_sync import main
if __name__ == "__main__":
    raise SystemExit(main())
