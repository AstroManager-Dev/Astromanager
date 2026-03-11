PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

ALTER TABLE raw_files ADD COLUMN file_role TEXT;
ALTER TABLE raw_files ADD COLUMN classification_rule TEXT;
ALTER TABLE raw_files ADD COLUMN quality_flag TEXT;

CREATE INDEX IF NOT EXISTS idx_raw_files_file_role
  ON raw_files(file_role);

CREATE INDEX IF NOT EXISTS idx_raw_files_classification_rule
  ON raw_files(classification_rule);

CREATE INDEX IF NOT EXISTS idx_raw_files_quality_flag
  ON raw_files(quality_flag);

UPDATE raw_files
SET
  file_role = 'metadata',
  classification_rule = 'dwarf_metadata_json',
  quality_flag = NULL
WHERE file_name = 'shotsInfo.json'
  AND (
    source_subtype = 'dwarf_metadata'
    OR rel_path LIKE '%/shotsInfo.json'
  );

UPDATE raw_files
SET
  file_role = 'preview',
  classification_rule = 'dwarf_preview_asset',
  quality_flag = NULL
WHERE (
    source_subtype = 'dwarf_preview'
    OR file_name IN (
      'stacked.jpg',
      'stacked_thumbnail.jpg',
      'img_reference.png',
      'img_stacked_counter.png',
      'img_stacked_all.tif'
    )
    OR file_name LIKE '%.png'
    OR file_name LIKE '%.jpg'
    OR file_name LIKE '%.jpeg'
    OR file_name LIKE '%.tif'
    OR file_name LIKE '%.tiff'
  )
  AND is_dwarf_generated = 1;

UPDATE raw_files
SET
  file_role = 'light',
  classification_rule = 'dwarf_stacked_fits',
  quality_flag = 'dwarf_generated_stack',
  is_session_input = 0,
  is_dwarf_generated = 1,
  derivative_kind = 'dwarf_stacked_fits'
WHERE file_name LIKE 'stacked-%'
  AND file_name LIKE '%.fits';

UPDATE raw_files
SET
  file_role = 'light',
  classification_rule = 'dwarf_failed_light',
  quality_flag = 'dwarf_rejected',
  is_session_input = 1,
  derivative_kind = 'light_raw_frame'
WHERE file_name LIKE 'failed_%'
  AND file_name LIKE '%.fits';

UPDATE raw_files
SET
  file_role = 'light',
  classification_rule = 'light_raw_frame',
  quality_flag = COALESCE(quality_flag, NULL),
  is_session_input = 1,
  derivative_kind = 'light_raw_frame'
WHERE file_name LIKE '%.fits'
  AND file_name NOT LIKE 'failed_%'
  AND file_name NOT LIKE 'stacked-%'
  AND (
    source_subtype = 'light_raw_frame'
    OR derivative_kind = 'light_raw_frame'
    OR is_session_input = 1
  );

UPDATE raw_files
SET
  file_role = 'dark',
  classification_rule = COALESCE(classification_rule, 'dark_raw_frame'),
  quality_flag = COALESCE(quality_flag, NULL)
WHERE source_subtype = 'dark_raw_frame'
   OR rel_path LIKE '%/DWARF_DARK/%';

UPDATE raw_files
SET
  file_role = 'bias',
  classification_rule = COALESCE(classification_rule, 'cali_frame_bias'),
  quality_flag = COALESCE(quality_flag, NULL)
WHERE source_domain = 'cali_frame'
  AND source_subtype = 'bias';

UPDATE raw_files
SET
  file_role = 'flat',
  classification_rule = COALESCE(classification_rule, 'cali_frame_flat'),
  quality_flag = COALESCE(quality_flag, NULL)
WHERE source_domain = 'cali_frame'
  AND source_subtype = 'flat';

UPDATE raw_files
SET
  file_role = 'dark',
  classification_rule = COALESCE(classification_rule, 'cali_frame_dark'),
  quality_flag = COALESCE(quality_flag, NULL)
WHERE source_domain = 'cali_frame'
  AND source_subtype = 'dark';

COMMIT;
PRAGMA foreign_keys = ON;
