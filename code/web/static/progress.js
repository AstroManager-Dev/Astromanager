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

  const featuredNameEl = document.getElementById("featured-run-name");
  const featuredHeroEl = document.getElementById("featured-run-hero");
  const featuredNoteEl = document.getElementById("featured-run-note");
  const featuredStatusEl = document.getElementById("featured-run-status");
  const featuredStartedEl = document.getElementById("featured-run-started");
  const featuredWorkflowEl = document.getElementById("featured-run-workflow");
  const featuredStepEl = document.getElementById("featured-run-step");
  const featuredActiveCountEl = document.getElementById("featured-run-active-count");
  const featuredMetricsEl = document.getElementById("featured-run-metrics");
  const featuredMetricLabels = [1,2,3,4].map((i) => document.getElementById(`featured-metric-label-${i}`));
  const featuredMetricValues = [1,2,3,4].map((i) => document.getElementById(`featured-metric-value-${i}`));

  let timer = null;

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
      <article class="run-card run-card--improved">
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

  function noteMetric(note, key) {
    const match = String(note || '').match(new RegExp(`(?:^|[,\s])${key}=([^,\s]+)`));
    return match ? match[1] : null;
  }


  function buildFeaturedMetrics(progress, featuredRun) {
    const workflow = String(progress.workflow || featuredRun?.job_name || '').toLowerCase();
    const note = featuredRun?.note || '';
    if (workflow.includes('raw_sync')) {
      return [
        ['Geplant', progress.plan_count],
        ['Geladen', progress.downloaded],
        ['Skip', progress.skipped],
        ['Fehler', progress.errors],
      ].filter((item) => item[1] !== undefined && item[1] !== null);
    }
    if (workflow.includes('index')) {
      return [
        ['Indexed', progress.files_indexed ?? noteMetric(note, 'files_indexed')],
        ['Hashes', progress.files_hashed ?? noteMetric(note, 'files_hashed')],
        ['Reused', progress.files_reused ?? noteMetric(note, 'files_reused')],
        ['Skipped', progress.skipped ?? noteMetric(note, 'sessions_skipped_unchanged')],
      ].filter((item) => item[1] !== undefined && item[1] !== null);
    }
    if (workflow.includes('master_darks')) {
      return [
        ['Gruppen', progress.group_count],
        ['Erstellt', progress.created_count],
        ['Skip', progress.skipped],
        ['Fehler', progress.errors],
      ].filter((item) => item[1] !== undefined && item[1] !== null);
    }
    if (workflow.includes('siril')) {
      return [
        ['Sessions', progress.sessions_total],
        ['Fertig', progress.sessions_done],
        ['Skip', progress.skipped],
        ['Fehler', progress.errors],
      ].filter((item) => item[1] !== undefined && item[1] !== null);
    }
    return [];
  }

  function applyFeaturedMetrics(metrics) {
    if (!featuredMetricsEl) return;
    if (!metrics.length) {
      featuredMetricsEl.hidden = true;
      featuredMetricLabels.forEach((el) => setText(el, ''));
      featuredMetricValues.forEach((el) => setText(el, ''));
      return;
    }
    featuredMetricsEl.hidden = false;
    for (let i = 0; i < 4; i += 1) {
      const item = metrics[i];
      setText(featuredMetricLabels[i], item ? item[0] : '');
      setText(featuredMetricValues[i], item ? item[1] : '');
    }
  }

  function applyFeaturedSummary(data) {
    const progress = data.progress || {};
    const active = Boolean(progress.active);
    const currentJob = data.current_job || null;
    const recentRuns = data.recent_runs || [];
    const featuredRun = active ? currentJob : (recentRuns[0] || currentJob);
    const pct = typeof progress.progress_pct === 'number'
      ? Math.max(0, Math.min(100, progress.progress_pct))
      : (featuredRun && String(featuredRun.status || '').toLowerCase() === 'done' ? 100 : 0);

    setText(featuredNameEl, featuredRun?.job_name || data.title || 'Bereit');
    setText(featuredNoteEl, featuredRun?.note || data.subtitle || 'Kein aktiver Job');
    setText(featuredStartedEl, featuredRun?.started_at || 'Kein aktiver Run');
    setText(featuredWorkflowEl, progress.workflow || featuredRun?.job_name || 'idle');
    setText(featuredStepEl, progress.current_step || '—');
    setText(featuredActiveCountEl, (data.active_runs || []).length || 0);

    if (featuredStatusEl) {
      const status = (featuredRun?.status || (active ? 'running' : 'idle')).toString();
      featuredStatusEl.textContent = status;
      featuredStatusEl.className = `status-pill status-${status.toLowerCase()}`;
    }
    if (featuredHeroEl) {
      featuredHeroEl.classList.toggle('is-running', active);
    }
    applyFeaturedMetrics(buildFeaturedMetrics(progress, featuredRun).slice(0, 4));
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
      applyFeaturedSummary(data);
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
    tick();
    timer = setInterval(tick, 1800);
  }

  function stopLive(fetchOnce) {
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
