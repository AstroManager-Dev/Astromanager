# Web-Refactor: app.py verschlankt

## Umsetzung
- Neue Modulstruktur unter `code/web/functions/`.
- `app.py` auf App-Setup, Context-Processor und Routen reduziert.
- Fachlogiken ausgelagert nach:
  - `functions/common.py`
  - `functions/program_info.py`
  - `functions/database.py`
  - `functions/status.py`
  - `functions/targets.py`
  - `functions/gallery.py`
  - `functions/formatters.py`
- Header-Version und Programm-Info-Templates bereinigt.
- Dictionary-Zugriffe in Jinja auf explizite Schlüssel umgestellt.
