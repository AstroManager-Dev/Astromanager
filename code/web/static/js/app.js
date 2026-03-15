(function () {
  const responseBox = document.getElementById("response-box");
  const statusBtn = document.getElementById("status-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  const bottomButtons = document.querySelectorAll(".bottom-nav-btn[data-tab]");
  const menuButtons = document.querySelectorAll(".sheet-link[data-tab]");
  const pathname = window.location.pathname || "/";
  const openMenuBtn = document.getElementById("open-menu-btn");
  const closeMenuBtn = document.getElementById("close-menu-btn");
  const menuSheet = document.getElementById("menu-sheet");
  const menuBackdrop = document.getElementById("menu-backdrop");
  const validTabs = ["gallery", "atlas", "targets", "overview", "settings", "logs", "info", "admin", "dev", "database"];

  function showResponse(text) {
    if (!responseBox) return;
    responseBox.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  }

  function showToast(message, ok = true) {
    let box = document.querySelector('.toast-box');
    if (!box) {
      box = document.createElement('div');
      box.className = 'toast-box';
      document.body.appendChild(box);
    }
    const toast = document.createElement('div');
    toast.className = 'toast ' + (ok ? 'toast-ok' : 'toast-error');
    toast.textContent = message;
    box.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('visible'));
    setTimeout(() => {
      toast.classList.remove('visible');
      setTimeout(() => toast.remove(), 250);
    }, 2800);
  }

  function hashForTab(name) {
    return `#${name}`;
  }

  function setActiveTabButton(name) {
    bottomButtons.forEach((btn) => {
      const isActive = btn.dataset.tab === name;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    menuButtons.forEach((btn) => {
      const isActive = btn.dataset.tab === name;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });
  }

  function closeMenu() {
    if (!menuSheet || !menuBackdrop || !openMenuBtn) return;
    menuSheet.classList.remove("open");
    menuSheet.setAttribute("aria-hidden", "true");
    menuBackdrop.hidden = true;
    openMenuBtn.setAttribute("aria-expanded", "false");
  }

  function openMenu() {
    if (!menuSheet || !menuBackdrop || !openMenuBtn) return;
    menuSheet.classList.add("open");
    menuSheet.setAttribute("aria-hidden", "false");
    menuBackdrop.hidden = false;
    openMenuBtn.setAttribute("aria-expanded", "true");
  }

  function activateTab(name) {
    const next = validTabs.includes(name) ? name : 'overview';
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === next));
    setActiveTabButton(next);
    history.replaceState(null, "", hashForTab(next));
    closeMenu();
  }

  async function runAction(action) {
    showResponse("Läuft …");
    try {
      const res = await fetch(`/api/run/${action}`, { method: "POST" });
      const data = await res.json();
      showResponse(data);
      if (data.ok === false) {
        showToast(data.error || data.stderr || 'Aktion fehlgeschlagen.', false);
      } else {
        showToast((data.details && data.details.message) || 'Aktion gestartet.', true);
      }
      document.dispatchEvent(new CustomEvent("astro:action-finished", { detail: { action, data } }));
    } catch (err) {
      const msg = `Fehler: ${err}`;
      showResponse(msg);
      showToast(msg, false);
    }
  }

  async function loadStatus() {
    showResponse("Lade Status …");
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      const data = await res.json();
      showResponse(data);
    } catch (err) {
      showResponse(`Fehler: ${err}`);
    }
  }

  document.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", () => runAction(btn.dataset.action));
  });

  [...bottomButtons, ...menuButtons, ...document.querySelectorAll('[data-tab]')].forEach((btn) => {
    btn.addEventListener('click', (event) => {
      const tab = btn.dataset.tab;
      if (!tab || btn.id === 'open-menu-btn') return;
      event.preventDefault();
      if (!tabPanels.length) {
        window.location.href = `/#${tab}`;
        return;
      }
      activateTab(tab);
    });
  });

  if (statusBtn) statusBtn.addEventListener("click", loadStatus);
  if (openMenuBtn) openMenuBtn.addEventListener("click", (e) => { e.preventDefault(); openMenu(); });
  if (closeMenuBtn) closeMenuBtn.addEventListener("click", closeMenu);
  if (menuBackdrop) menuBackdrop.addEventListener("click", closeMenu);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });

  async function restoreArchive(name){
    const res = await fetch(`/api/dev/restore/${encodeURIComponent(name)}`, {method:'POST'});
    const data = await res.json();
    showToast(data.ok ? `Restore fertig: ${name}` : `Restore fehlgeschlagen: ${data.error || data.stderr || 'Unbekannter Fehler'}`, !!data.ok);
    if (data.ok) setTimeout(() => window.location.reload(), 1000);
  }
  document.querySelectorAll('[data-restore]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const name = btn.dataset.restore;
      if (name && confirm(`Backup wirklich zurückspielen?
${name}`)) {
        restoreArchive(name);
      }
    });
  });

  async function deleteArtifact(bucket, name){
    const res = await fetch(`/api/dev/delete/${encodeURIComponent(bucket)}/${encodeURIComponent(name)}`, {method:'POST'});
    const data = await res.json();
    showToast(data.ok ? ((data.details && data.details.message) || `Gelöscht: ${name}`) : `Löschen fehlgeschlagen: ${data.error || data.stderr || 'Unbekannter Fehler'}`, !!data.ok);
    if (data.ok) setTimeout(() => window.location.reload(), 800);
  }
  document.querySelectorAll('[data-delete]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const bucket = btn.dataset.delete;
      const name = btn.dataset.filename;
      if (bucket && name && confirm(`Datei wirklich löschen?
${name}`)) {
        deleteArtifact(bucket, name);
      }
    });
  });

  document.querySelectorAll('.upload-form').forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = new FormData(form);
      const res = await fetch(form.action, {method:'POST', body});
      const data = await res.json();
      showToast(data.ok ? ((data.details && data.details.message) || 'ZIP erfolgreich eingespielt.') : `ZIP-Import fehlgeschlagen: ${data.error || data.stderr || 'Unbekannter Fehler'}`, !!data.ok);
      if (data.ok) setTimeout(() => window.location.reload(), 1000);
    });
  });

  const hash = (window.location.hash || '#gallery').replace(/^#/, '');
  if (tabPanels.length) {
    activateTab(validTabs.includes(hash) ? hash : 'gallery');
    return;
  }

  let fallbackTab = 'gallery';
  if (pathname.startsWith('/targets/')) {
    fallbackTab = 'targets';
  }

  setActiveTabButton(fallbackTab);
})();
