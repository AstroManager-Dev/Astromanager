#!/usr/bin/env python3
# AstroManager
# Author: M. Pastor Nause
import os
import sys
APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY = os.path.join(APP_ROOT, "lib", "py")
if LIB_PY not in sys.path:
    sys.path.insert(0, LIB_PY)
from astromanager.raw.plan_sync import main as plan_main

def main(argv=None):
    return plan_main(argv or sys.argv[1:])

if __name__ == "__main__":
    raise SystemExit(main())
