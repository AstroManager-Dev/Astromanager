(function () {
  const responseBox = document.getElementById("response-box");
  const statusBtn = document.getElementById("status-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  const bottomButtons = document.querySelectorAll(".bottom-nav-btn[data-tab]");
  const menuButtons = document.querySelectorAll(".sheet-link[data-tab]");
  const pathname = window.location.pathname || "/";
  const openMenuBtns = document.querySelectorAll("#open-menu-btn, #open-menu-btn-bottom");
  const closeMenuBtn = document.getElementById("close-menu-btn");
  const menuSheet = document.getElementById("menu-sheet");
  const menuBackdrop = document.getElementById("menu-backdrop");
  const validTabs = ["gallery", "atlas", "targets", "overview", "logs", "info", "admin", "dev", "database"];

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
    if (!menuSheet || !menuBackdrop) return;
    menuSheet.classList.remove("open");
    menuSheet.setAttribute("aria-hidden", "true");
    menuBackdrop.hidden = true;
    openMenuBtns.forEach((btn) => btn.setAttribute("aria-expanded", "false"));
  }

  function openMenu() {
    if (!menuSheet || !menuBackdrop) return;
    menuSheet.classList.add("open");
    menuSheet.setAttribute("aria-hidden", "false");
    menuBackdrop.hidden = false;
    openMenuBtns.forEach((btn) => btn.setAttribute("aria-expanded", "true"));
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
  openMenuBtns.forEach((btn) => btn.addEventListener("click", (e) => { e.preventDefault(); openMenu(); }));
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


  function initSegmentSwitches() {
    const groups = document.querySelectorAll('[data-switch-group]');
    groups.forEach((groupEl) => {
      const group = groupEl.dataset.switchGroup;
      if (!group) return;
      const buttons = document.querySelectorAll(`[data-switch-group="${group}"][data-switch-target]`);
      const panels = document.querySelectorAll(`[data-switch-panel="${group}"]`);
      const activate = (value) => {
        buttons.forEach((btn) => {
          const active = btn.dataset.switchTarget === value;
          btn.classList.toggle('active', active);
          btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        panels.forEach((panel) => panel.classList.toggle('active', panel.dataset.switchValue === value));
      };
      const defaultValue = groupEl.dataset.switchDefault || (buttons[0] && buttons[0].dataset.switchTarget) || '';
      buttons.forEach((btn) => {
        if (btn.disabled) return;
        btn.addEventListener('click', () => activate(btn.dataset.switchTarget));
      });
      if (defaultValue) activate(defaultValue);
    });
  }

  initSegmentSwitches();

  const hash = (window.location.hash || '#gallery').replace(/^#/, '');
  if (tabPanels.length) {
    activateTab(validTabs.includes(hash) ? hash : 'gallery');
    return;
  }

  let fallbackTab = 'gallery';
  if (pathname.startsWith('/targets/')) {
    fallbackTab = 'targets';
  } else if (pathname.startsWith('/settings')) {
    fallbackTab = '';
  }

  setActiveTabButton(fallbackTab);
})();
