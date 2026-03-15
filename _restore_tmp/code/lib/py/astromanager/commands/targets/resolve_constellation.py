#!/usr/bin/env python3
import sys

from astromanager.targets.constellation_resolver import run


def main(argv=None):
    argv = argv or sys.argv[1:]
    only_new = "--all" not in argv
    limit = 1000

    if "--limit" in argv:
        idx = argv.index("--limit")
        if idx + 1 < len(argv):
            limit = max(1, int(argv[idx + 1]))

    print("target_constellation_resolver_module=astromanager.targets.constellation_resolver")
    return run(only_new=only_new, limit=limit)


if __name__ == "__main__":
    raise SystemExit(main())
