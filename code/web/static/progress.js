(function () {
  const statusEl = document.getElementById("live-progress-status");
  const metaEl = document.getElementById("live-progress-meta");
  const barEl = document.getElementById("live-progress-bar");
  const tailEl = document.getElementById("live-progress-tail");
  const pathEl = document.getElementById("live-progress-path");
  const webLogEl = document.getElementById("web-log-box");
  const runsCardsEl = document.getElementById("runs-cards");
  const statusRunsCardsEl = document.getElementById("status-runs-cards");
  const backupGridEl = document.getElementById("backup-files-grid");
  const sqlGridEl = document.getElementById("sql-files-grid");

  let timer = null;
  let liveActive = false;

  if (!statusEl || !metaEl || !barEl || !tailEl || !pathEl) return;

  function setText(el, value) {
    if (el) el.textContent = value == null ? "" : String(value);
  }

  function buildMeta(progress) {
    const workflow = progress.workflow || "idle";
    if (workflow === "raw_sync") {
      return [
        `Workflow: RAW Sync`,
        `Geplant: ${progress.plan_count ?? 0}`,
        `Verarbeitet: ${progress.processed_count ?? 0}`,
        `Geladen: ${progress.downloaded ?? 0}`,
        `Skip: ${progress.skipped ?? 0}`,
        `Fehler: ${progress.errors ?? 0}`,
      ].join(" • ");
    }
    return [
      `Workflow: ${workflow}`,
      `Dateien: ${progress.files_indexed ?? 0}/${progress.files_total ?? 0}`,
      `Sessions: ${progress.sessions_indexed ?? 0}`,
      `Kalibrierung: ${progress.cal_assets_indexed ?? 0}`,
      progress.current_step ? `Step: ${progress.current_step}` : null,
    ].filter(Boolean).join(" • ");
  }

  function renderRuns(target, runs) {
    if (!target) return;
    if (!runs || !runs.length) {
      target.innerHTML = '<article class="run-card empty">Keine Runs vorhanden.</article>';
      return;
    }
    target.innerHTML = runs.slice(0, 8).map((run) => `
      <article class="run-card">
        <div class="run-card-top">
          <strong>${run.job_name || "Job"}</strong>
          <span class="status-pill status-${String(run.status || "").toLowerCase()}">${run.status || "—"}</span>
        </div>
        <div class="muted">${run.started_at || "—"}${run.finished_at ? ` → ${run.finished_at}` : ""}</div>
        <div class="run-note">${run.note || run.source || "—"}</div>
      </article>`).join("");
  }

  function renderFileGrid(target, items, bucket) {
    if (!target) return;
    if (!items || !items.length) {
      target.innerHTML = `<article class="file-card empty">Keine ${bucket === 'backup' ? 'Backups' : 'SQL-Dumps'} gefunden.</article>`;
      return;
    }
    target.innerHTML = items.map((item) => `
      <article class="file-card">
        <strong>${item.name}</strong>
        <div class="muted">${item.size_label || ""}</div>
        <a class="mini-btn file-download" href="/download/${bucket}/${encodeURIComponent(item.name)}">Download</a>
      </article>`).join("");
  }

  async function fetchDevFiles() {
    try {
      const res = await fetch('/api/dev/files', { cache: 'no-store' });
      const data = await res.json();
      if (data.ok) {
        renderFileGrid(backupGridEl, data.backups, 'backup');
        renderFileGrid(sqlGridEl, data.sql_dumps, 'sql');
      }
    } catch (_) {}
  }

  async function refreshSummary() {
    try {
      const res = await fetch('/api/live/summary', { cache: 'no-store' });
      const data = await res.json();
      if (!data.ok) return false;
      const progress = data.progress || {};
      setText(statusEl, progress.status || 'Bereit.');
      setText(metaEl, buildMeta(progress));
      setText(pathEl, progress.log_path || '');
      setText(tailEl, progress.tail || 'Noch keine Live-Daten.');
      if (webLogEl && data.latest_log !== undefined) setText(webLogEl, data.latest_log || 'Kein Log vorhanden.');
      const pct = typeof progress.progress_pct === 'number' ? progress.progress_pct : 0;
      barEl.style.width = `${pct}%`;
      barEl.textContent = pct > 10 ? `${pct}%` : '';
      renderRuns(runsCardsEl, data.recent_runs || []);
      renderRuns(statusRunsCardsEl, data.recent_runs || []);
      return Boolean(progress.active);
    } catch (_) {
      return false;
    }
  }

  async function tick() {
    const isRunning = await refreshSummary();
    if (!isRunning) stopLive(true);
  }

  function startLive() {
    if (timer) clearInterval(timer);
    liveActive = true;
    tick();
    timer = setInterval(tick, 1800);
  }

  function stopLive(fetchOnce) {
    liveActive = false;
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    if (fetchOnce) {
      refreshSummary();
      fetchDevFiles();
    }
  }

  document.addEventListener('astro:action-finished', (event) => {
    const data = event.detail && event.detail.data;
    if (data && data.ok) startLive();
    else stopLive(true);
  });

  refreshSummary().then((isRunning) => {
    if (isRunning) startLive();
    else stopLive(false);
    fetchDevFiles();
  });
})();
