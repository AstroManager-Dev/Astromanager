#!/usr/bin/env python3
import os
import sys

APP_ROOT = os.environ.get("APP_ROOT", "/app")
LIB_PY_ROOT = os.path.join(APP_ROOT, "lib", "py")
if LIB_PY_ROOT not in sys.path:
    sys.path.insert(0, LIB_PY_ROOT)

from astromanager.commands.targets.resolve_wikidata_names import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
