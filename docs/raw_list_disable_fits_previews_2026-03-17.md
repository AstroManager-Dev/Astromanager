# RAW-Liste ohne FITS-Viewer-Thumbnails

Ziel:
- Session-RAW-Liste bewusst ohne serverseitige FITS-Vorschaubilder rendern
- Detailseite behält den FITS-Viewer
- Listenansicht wird auf großen Sessions entlastet

Änderungen:
- `code/web/templates/pages/session_raw_list/_file_item.html`
- `code/web/static/css/app.css`

Hinweis Backup/Tailscale:
- Das Backup-Skript scheitert aktuell an root-eigenen Dateien unter `config/tailscale`
- Für No-Media-Backups den Pfad entweder ausnehmen oder mit sudo/angepassten Rechten arbeiten
