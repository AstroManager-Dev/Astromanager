(function () {
  const responseBox = document.getElementById("response-box");
  const actionButtons = document.querySelectorAll("[data-action]");
  const statusBtn = document.getElementById("status-btn");
  const tabButtons = document.querySelectorAll("[data-tab]");
  const tabPanels = document.querySelectorAll(".tab-panel");
  const burgerBtn = document.getElementById("burger-btn");
  const menuPanel = document.getElementById("menu-panel");

  function showResponse(text) {
    if (!responseBox) return;
    responseBox.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  }

  async function runAction(action) {
    showResponse("Läuft …");
    const res = await fetch(`/api/run/${action}`, { method: "POST" });
    const data = await res.json();
    showResponse(data);
  }

  async function loadStatus() {
    showResponse("Lade Status …");
    const res = await fetch("/api/status");
    const data = await res.json();
    showResponse(data);
  }

  function hashForTab(name) {
    if (name === "database") return "#database";
    if (name === "targets") return "#targets";
    return "#overview";
  }

  function activateTab(name) {
    tabButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === name));
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === name));
    history.replaceState(null, "", hashForTab(name));

    if (menuPanel) menuPanel.classList.remove("open");
    if (burgerBtn) burgerBtn.setAttribute("aria-expanded", "false");
  }

  actionButtons.forEach((btn) => {
    btn.addEventListener("click", () => runAction(btn.dataset.action));
  });

  if (statusBtn) {
    statusBtn.addEventListener("click", loadStatus);
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
  });

  if (burgerBtn && menuPanel) {
    burgerBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      const isOpen = menuPanel.classList.toggle("open");
      burgerBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    document.addEventListener("click", (event) => {
      if (!menuPanel.contains(event.target) && !burgerBtn.contains(event.target)) {
        menuPanel.classList.remove("open");
        burgerBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  if (window.location.hash === "#database") activateTab("database");
  else if (window.location.hash === "#targets") activateTab("targets");
  else activateTab("overview");
})();
