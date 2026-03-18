ALTER TABLE app_users ADD COLUMN must_set_password INTEGER NOT NULL DEFAULT 0;
ALTER TABLE app_users ADD COLUMN is_builtin INTEGER NOT NULL DEFAULT 0;
ALTER TABLE app_users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE app_users ADD COLUMN locked_until TEXT NOT NULL DEFAULT '';
ALTER TABLE app_users ADD COLUMN password_updated_at TEXT NOT NULL DEFAULT '';
ALTER TABLE app_users ADD COLUMN last_login_ip TEXT NOT NULL DEFAULT '';

INSERT INTO app_users (username, display_name, password_hash, is_active, note, must_set_password, is_builtin, created_at, updated_at)
VALUES ('admin', 'Administrator', '', 1, 'Bootstrap-Admin. Passwort muss beim ersten Login gesetzt werden.', 1, 1, datetime('now'), datetime('now'))
ON CONFLICT(username) DO UPDATE SET
  display_name=excluded.display_name,
  note=excluded.note,
  is_builtin=1,
  updated_at=datetime('now');

INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by)
SELECT u.id, r.id, datetime('now'), 'migration-0005'
FROM app_users u
JOIN roles r ON r.code='admin'
WHERE lower(u.username)='admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur
    WHERE ur.user_id = u.id AND ur.role_id = r.id
  );
