BEGIN TRANSACTION;

UPDATE sessions
SET
  subtype = COALESCE(subtype, 'tele'),
  session_kind = COALESCE(session_kind, 'light_session'),
  target_source = COALESCE(target_source, 'folder_name'),
  solve_status = CASE
    WHEN COALESCE(solve_status, '') IN ('', 'review') THEN 'named'
    ELSE solve_status
  END,
  needs_review = COALESCE(needs_review, 0),
  needs_plate_solving = COALESCE(needs_plate_solving, 0),
  treat_as_normal_light = COALESCE(treat_as_normal_light, 1),
  classification_rule = COALESCE(classification_rule, 'tele_named_target')
WHERE raw_session_path LIKE '%/DWARF_RAW_TELE_%_EXP_%'
  AND raw_session_path NOT LIKE '%/DWARF_RAW_TELE_Sun_EXP_%'
  AND raw_session_path NOT LIKE '%/DWARF_RAW_TELE_Moon_EXP_%'
  AND raw_session_path NOT LIKE '%/DWARF_RAW_TELE_Unknown_EXP_%'
  AND raw_session_path NOT LIKE '%/DWARF_RAW_TELE_EXP_%';

UPDATE sessions
SET
  category = 'sun',
  subtype = 'tele',
  session_kind = 'light_session',
  target = 'Sun',
  target_source = 'folder_name',
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 1,
  classification_rule = 'tele_sun'
WHERE raw_session_path LIKE '%/DWARF_RAW_TELE_Sun_EXP_%';

UPDATE sessions
SET
  category = 'moon',
  subtype = 'tele',
  session_kind = 'light_session',
  target = 'Moon',
  target_source = 'folder_name',
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 1,
  classification_rule = 'tele_moon'
WHERE raw_session_path LIKE '%/DWARF_RAW_TELE_Moon_EXP_%';

UPDATE sessions
SET
  category = 'deepsky',
  subtype = 'tele',
  session_kind = 'light_session',
  target = 'UNKNOWN',
  target_source = 'folder_name_unknown',
  solve_status = 'unsolved',
  needs_review = 0,
  needs_plate_solving = 1,
  treat_as_normal_light = 1,
  classification_rule = 'tele_unknown_target'
WHERE raw_session_path LIKE '%/DWARF_RAW_TELE_Unknown_EXP_%';

UPDATE sessions
SET
  category = 'unknown',
  subtype = 'tele',
  session_kind = 'light_session',
  target_source = 'missing_in_name',
  solve_status = 'review',
  needs_review = 1,
  needs_plate_solving = 0,
  treat_as_normal_light = 1,
  classification_rule = 'tele_missing_target'
WHERE raw_session_path LIKE '%/DWARF_RAW_TELE_EXP_%';

UPDATE sessions
SET
  category = 'calibration',
  subtype = 'dwarf_dark',
  session_kind = 'raw_dark_pool',
  target_source = 'not_applicable',
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 0,
  classification_rule = 'dwarf_dark_root'
WHERE raw_session_path LIKE '%/DWARF_DARK%';

UPDATE sessions
SET
  category = 'calibration',
  subtype = 'cali_frame',
  session_kind = 'calibration_pool',
  target_source = 'not_applicable',
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 0,
  classification_rule = 'cali_frame_root'
WHERE raw_session_path LIKE '%/CALI_FRAME%';

UPDATE sessions
SET
  category = 'derived',
  subtype = 'restacked',
  session_kind = 'derived_output',
  target_source = COALESCE(target_source, 'derived_path'),
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 0,
  classification_rule = 'restacked'
WHERE raw_session_path LIKE '%/RESTACKED/%';

UPDATE sessions
SET
  category = 'review',
  subtype = 'solving_failed',
  session_kind = 'failed_session',
  target_source = COALESCE(target_source, 'derived_path'),
  solve_status = 'review',
  needs_review = 1,
  needs_plate_solving = 0,
  treat_as_normal_light = 0,
  classification_rule = 'solving_failed'
WHERE raw_session_path LIKE '%/Solving_Failed/%';

UPDATE sessions
SET
  category = 'startrails',
  subtype = 'tele',
  session_kind = 'special_session',
  target_source = COALESCE(target_source, 'folder_name'),
  solve_status = 'na',
  needs_review = 0,
  needs_plate_solving = 0,
  treat_as_normal_light = 0,
  classification_rule = 'startrails'
WHERE raw_session_path LIKE '%STARTRAILS%';

COMMIT;
