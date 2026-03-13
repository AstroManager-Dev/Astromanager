(function () {
  const responseBox = document.getElementById("response-box");
  const statusBtn = document.getElementById("status-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  const tabButtons = document.querySelectorAll("[data-tab]");
  const bottomButtons = document.querySelectorAll(".bottom-nav-btn[data-tab]");
  const openMenuBtn = document.getElementById("open-menu-btn");
  const closeMenuBtn = document.getElementById("close-menu-btn");
  const openMoreBtn = document.getElementById("open-more-btn");
  const menuSheet = document.getElementById("menu-sheet");
  const menuBackdrop = document.getElementById("menu-backdrop");

  function showResponse(text) {
    if (!responseBox) return;
    responseBox.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  }

  function hashForTab(name) {
    return `#${name}`;
  }

  function setActiveTabButton(name) {
    bottomButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === name));
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
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === name));
    setActiveTabButton(name);
    history.replaceState(null, "", hashForTab(name));
    closeMenu();
  }

  async function runAction(action) {
    showResponse("Läuft …");
    try {
      const res = await fetch(`/api/run/${action}`, { method: "POST" });
      const data = await res.json();
      showResponse(data);
      document.dispatchEvent(new CustomEvent("astro:action-finished", { detail: { action, data } }));
    } catch (err) {
      showResponse(`Fehler: ${err}`);
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

  document.querySelectorAll("[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.id === "open-more-btn") return;
      activateTab(btn.dataset.tab);
    });
  });

  if (statusBtn) statusBtn.addEventListener("click", loadStatus);
  if (openMenuBtn) openMenuBtn.addEventListener("click", openMenu);
  if (closeMenuBtn) closeMenuBtn.addEventListener("click", closeMenu);
  if (menuBackdrop) menuBackdrop.addEventListener("click", closeMenu);
  if (openMoreBtn) openMoreBtn.addEventListener("click", openMenu);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenu();
  });

  const hash = (window.location.hash || "#overview").replace(/^#/, "");
  activateTab(["overview", "gallery", "status", "dev", "admin"].includes(hash) ? hash : "overview");
})();
