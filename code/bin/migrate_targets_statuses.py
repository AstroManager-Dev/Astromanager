#!/usr/bin/env python3
from pathlib import Path

p = Path("/home/pi/docker/astromanager/code/lib/db.sh")
s = p.read_text()

marker = 'db_exec "CREATE INDEX IF NOT EXISTS idx_targets_ra_dec ON targets(ra_deg, dec_deg);"'
if marker not in s:
    raise SystemExit("marker not found in db.sh")

insert = '''
  for c in coord_status name_status name_source name_resolved_at; do
    if ! db_column_exists targets "$c"; then
      case "$c" in
        coord_status) db_exec "ALTER TABLE targets ADD COLUMN coord_status TEXT NOT NULL DEFAULT 'pending';" ;;
        name_status) db_exec "ALTER TABLE targets ADD COLUMN name_status TEXT NOT NULL DEFAULT 'pending';" ;;
        name_source) db_exec "ALTER TABLE targets ADD COLUMN name_source TEXT NOT NULL DEFAULT '';" ;;
        name_resolved_at) db_exec "ALTER TABLE targets ADD COLUMN name_resolved_at TEXT;" ;;
      esac
    fi
  done

  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_coord_status ON targets(coord_status);"
  db_exec "CREATE INDEX IF NOT EXISTS idx_targets_name_status ON targets(name_status);"
'''

if "idx_targets_coord_status" not in s:
    s = s.replace(marker, marker + "\n" + insert, 1)

p.write_text(s)
print("db.sh patched")
