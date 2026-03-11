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

      const indexed = data.files_indexed ?? 0;
      const total = data.files_total ?? 0;
      const hashed = data.files_hashed ?? 0;
      const reused = data.files_reused ?? 0;
      const calAssets = data.cal_assets_indexed ?? 0;
      const sessions = data.sessions_indexed ?? 0;

      const metaParts = [
        `Dateien verarbeitet: ${indexed}`,
        `Gesamt: ${total}`,
        `Gehasht: ${hashed}`,
        `Reuse: ${reused}`,
        `Kalibrierung: ${calAssets}`,
        `Sessions: ${sessions}`,
      ];
      setText(metaEl, metaParts.join(" • "));

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
