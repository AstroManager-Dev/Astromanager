PRAGMA foreign_keys = ON;

ALTER TABLE device_sources ADD COLUMN remote_base_dir TEXT NOT NULL DEFAULT '/Astronomy';
ALTER TABLE device_sources ADD COLUMN allowed_extensions TEXT NOT NULL DEFAULT '.fits,.fit,.fts';

CREATE TABLE IF NOT EXISTS device_instances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instance_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  source_id INTEGER NOT NULL,
  connection_kind TEXT NOT NULL DEFAULT 'ftp',
  host TEXT NOT NULL DEFAULT '',
  port INTEGER NOT NULL DEFAULT 21,
  auth_mode TEXT NOT NULL DEFAULT 'anonymous',
  username TEXT NOT NULL DEFAULT 'anonymous',
  password_text TEXT NOT NULL DEFAULT '',
  timeout_seconds INTEGER NOT NULL DEFAULT 15,
  remote_base_dir_override TEXT NOT NULL DEFAULT '',
  allowed_extensions_override TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  is_active INTEGER NOT NULL DEFAULT 1,
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (source_id) REFERENCES device_sources(id)
);

CREATE INDEX IF NOT EXISTS idx_device_instances_source_id ON device_instances(source_id);
CREATE INDEX IF NOT EXISTS idx_device_instances_active ON device_instances(is_active, is_default);

UPDATE device_sources
SET remote_base_dir = CASE source_key
      WHEN 'dwarflab_dwarf3' THEN '/Astronomy'
      WHEN 'dwarflab_dwarf2' THEN '/Astronomy'
      WHEN 'dwarflab_dwarf_mini' THEN '/Astronomy'
      WHEN 'zwo_seestar_s50' THEN '/Astronomy'
      ELSE remote_base_dir
    END,
    allowed_extensions = CASE source_key
      WHEN 'dwarflab_dwarf3' THEN '.fits,.fit,.fts,.jpg,.jpeg,.png,.json,.tif,.tiff'
      WHEN 'zwo_seestar_s50' THEN '.fits,.fit,.fts,.jpg,.jpeg,.png,.json'
      ELSE COALESCE(NULLIF(allowed_extensions, ''), '.fits,.fit,.fts')
    END;

INSERT INTO device_instances (
  id, instance_key, display_name, source_id, connection_kind, host, port,
  auth_mode, username, password_text, timeout_seconds, is_active, is_default,
  created_at, updated_at
)
SELECT
  1,
  'dwarflab_dwarf3',
  'DWARF 3',
  ds.id,
  'ftp',
  '192.168.2.163',
  21,
  'anonymous',
  'anonymous',
  '',
  15,
  1,
  1,
  datetime('now'),
  datetime('now')
FROM device_sources ds
WHERE ds.source_key = 'dwarflab_dwarf3'
  AND NOT EXISTS (
    SELECT 1 FROM device_instances di WHERE di.instance_key = 'dwarflab_dwarf3'
  );
