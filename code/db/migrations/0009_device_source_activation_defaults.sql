PRAGMA foreign_keys = ON;

UPDATE device_sources
SET is_active = CASE source_key
  WHEN 'dwarflab_dwarf3' THEN 1
  ELSE 0
END,
updated_at = datetime('now');
