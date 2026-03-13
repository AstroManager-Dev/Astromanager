(function () {
  const statusEl = document.getElementById("live-progress-status");
  const metaEl = document.getElementById("live-progress-meta");
  const barEl = document.getElementById("live-progress-bar");
  const tailEl = document.getElementById("live-progress-tail");
  const pathEl = document.getElementById("live-progress-path");

  if (!statusEl || !metaEl || !barEl || !tailEl || !pathEl) {
    return;
  }

  function setText(el, value) {
    el.textContent = value == null ? "" : String(value);
  }

  function buildMeta(data) {
    const workflow = data.workflow || "generic";

    if (workflow === "raw_sync") {
      const parts = [
        `Workflow: RAW Sync`,
        `Geplant: ${data.plan_count ?? 0}`,
        `Geladen: ${data.downloaded ?? 0}`,
        `Skip: ${data.skipped ?? 0}`,
        `Fehler: ${data.errors ?? 0}`,
      ];
      if (data.current_step) {
        parts.push(`Step: ${data.current_step}`);
      }
      return parts.join(" • ");
    }

    const parts = [
      `Workflow: ${workflow}`,
      `Dateien verarbeitet: ${data.files_indexed ?? 0}`,
      `Gesamt: ${data.files_total ?? 0}`,
      `Gehasht: ${data.files_hashed ?? 0}`,
      `Reuse: ${data.files_reused ?? 0}`,
      `Kalibrierung: ${data.cal_assets_indexed ?? 0}`,
      `Sessions: ${data.sessions_indexed ?? 0}`,
    ];

    if ((data.sessions_skipped_unchanged ?? 0) > 0) {
      parts.push(`Session-Skip: ${data.sessions_skipped_unchanged}`);
    }
    if (data.current_step) {
      parts.push(`Step: ${data.current_step}`);
    }

    return parts.join(" • ");
  }

  async function refreshProgress() {
    try {
      const res = await fetch("/api/progress/current", { cache: "no-store" });
      const data = await res.json();

      if (!data || !data.ok) {
        setText(statusEl, "Fortschritt konnte nicht geladen werden.");
        return;
      }

      setText(statusEl, data.status || "Bereit.");
      setText(pathEl, data.log_path || "");
      setText(metaEl, buildMeta(data));

      const pct = typeof data.progress_pct === "number" ? data.progress_pct : 0;
      barEl.style.width = `${pct}%`;
      barEl.textContent = pct > 8 ? `${pct}%` : "";

      setText(tailEl, data.tail || "");
    } catch (err) {
      setText(statusEl, `Fehler beim Laden des Fortschritts: ${err}`);
    }
  }

  refreshProgress();
  setInterval(refreshProgress, 2000);
})();
