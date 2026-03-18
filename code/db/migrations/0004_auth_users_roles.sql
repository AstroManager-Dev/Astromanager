CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 100,
  is_system INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS app_users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL DEFAULT '',
  is_active INTEGER NOT NULL DEFAULT 1,
  note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_login_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
  assigned_by TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES app_users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_roles_sort_order
  ON roles(sort_order, code);

CREATE INDEX IF NOT EXISTS idx_app_users_active
  ON app_users(is_active, username);

CREATE INDEX IF NOT EXISTS idx_user_roles_role_id
  ON user_roles(role_id, user_id);

INSERT INTO roles (id, code, label, description, sort_order, is_system)
VALUES
  (1, 'guest', 'Gast', 'Nicht angemeldet. Darf nur Galerie, Sessions, Targets, Atlas und Viewer sehen.', 10, 1),
  (2, 'observer', 'Observer', 'Angemeldeter Lese-Benutzer ohne Workflow-Rechte.', 20, 1),
  (3, 'user', 'User', 'Darf operative Workflows und Statusfunktionen nutzen.', 30, 1),
  (4, 'admin', 'Admin', 'Darf Einstellungen, Benutzer und Systemfunktionen verwalten.', 40, 1)
ON CONFLICT(code) DO UPDATE SET
  label=excluded.label,
  description=excluded.description,
  sort_order=excluded.sort_order,
  is_system=excluded.is_system,
  updated_at=datetime('now');
