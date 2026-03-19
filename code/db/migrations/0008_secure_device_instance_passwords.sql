PRAGMA foreign_keys = ON;

ALTER TABLE device_instances ADD COLUMN password_enc TEXT NOT NULL DEFAULT '';

UPDATE device_instances
SET password_enc = COALESCE(password_text, '')
WHERE COALESCE(password_enc, '') = '';
