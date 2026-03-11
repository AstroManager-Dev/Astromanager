from pathlib import Path

app_py = Path("/home/pi/docker/astromanager/code/web/app.py")
tpl = Path("/home/pi/docker/astromanager/code/web/templates/index.html")

app_text = app_py.read_text(encoding="utf-8", errors="replace")
tpl_text = tpl.read_text(encoding="utf-8", errors="replace")

import_line = "from progress_runtime import get_live_progress"
if import_line not in app_text:
    marker = "from actions import ACTION_HANDLERS"
    if marker not in app_text:
        raise SystemExit("Marker für Import in web/app.py nicht gefunden.")
    app_text = app_text.replace(marker, marker + "\nfrom progress_runtime import get_live_progress", 1)

route_block = """
@APP.get("/api/progress/current")
def api_progress_current():
    return jsonify(get_live_progress())
"""

if '@APP.get("/api/progress/current")' not in app_text:
    marker = '@APP.get("/api/status")'
    if marker not in app_text:
        raise SystemExit("Marker für Progress-Route in web/app.py nicht gefunden.")
    app_text = app_text.replace(marker, route_block + "\n\n" + marker, 1)

progress_card = """
  <section class="card" id="live-progress-card">
    <h2>Live-Fortschritt</h2>
    <div class="codebox" style="margin-bottom:12px;">
      <div id="live-progress-status">Warte auf Fortschritt ...</div>
      <div id="live-progress-meta" style="margin-top:10px; opacity:.9;"></div>
      <div style="margin-top:14px; background:#10131b; border-radius:999px; height:22px; overflow:hidden; border:1px solid rgba(255,255,255,.08);">
        <div id="live-progress-bar" style="height:100%; width:0%; background:#3a76b8; color:#fff; text-align:center; line-height:22px; white-space:nowrap; transition:width .35s ease;"></div>
      </div>
      <div id="live-progress-path" style="margin-top:10px; font-size:.92rem; opacity:.8; word-break:break-all;"></div>
    </div>
    <pre class="codebox" id="live-progress-tail" style="max-height:380px; overflow:auto;">Noch keine Live-Daten.</pre>
  </section>

"""

if 'id="live-progress-card"' not in tpl_text:
    marker = "Letztes Web-Log"
    if marker not in tpl_text:
        raise SystemExit("Marker 'Letztes Web-Log' im Template nicht gefunden.")
    tpl_text = tpl_text.replace(marker, progress_card + marker, 1)

script_tag = '<script src="/static/progress.js"></script>'
if script_tag not in tpl_text:
    end_marker = "</body>"
    if end_marker not in tpl_text:
        raise SystemExit("Kein </body> im Template gefunden.")
    tpl_text = tpl_text.replace(end_marker, f"  {script_tag}\n{end_marker}", 1)

app_py.write_text(app_text, encoding="utf-8")
tpl.write_text(tpl_text, encoding="utf-8")
print("web/app.py und Template für Live-Fortschritt gepatcht.")
