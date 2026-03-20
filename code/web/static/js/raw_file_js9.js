(function () {
  function bootJS9Shell(shell) {
    if (!shell || shell.dataset.js9Loaded === "1") {
      return;
    }
    if (typeof window.JS9 === "undefined" || typeof window.JS9.Load !== "function") {
      return;
    }

    const displayId = shell.dataset.js9Display || "JS9";
    const fitsUrl = shell.dataset.js9Url || "";
    if (!fitsUrl) {
      return;
    }

    shell.dataset.js9Loaded = "1";

    if (typeof window.JS9.globalOpts === "object" && window.JS9.globalOpts) {
      window.JS9.globalOpts.alerts = true;
      window.JS9.globalOpts.installDir = "/static/vendor/js9/";
      window.JS9.globalOpts.js9Helper = false;
    }

    const loadImage = function () {
      try {
        console.log("JS9 loading:", fitsUrl, "display:", displayId);
        window.JS9.Load(fitsUrl, {
          scale: "zscale",
          colormap: "grey",
          zoom: "tofit"
        }, {
          display: displayId
        });
      } catch (error) {
        console.error("JS9 load failed", error);
        shell.dataset.js9Loaded = "0";
      }
    };

    if (typeof window.JS9.GetDisplay === "function" && window.JS9.GetDisplay(displayId)) {
      loadImage();
      return;
    }

    let attempts = 0;
    const timer = window.setInterval(function () {
      attempts += 1;
      if (typeof window.JS9.GetDisplay === "function" && window.JS9.GetDisplay(displayId)) {
        window.clearInterval(timer);
        loadImage();
        return;
      }
      if (attempts >= 40) {
        window.clearInterval(timer);
        shell.dataset.js9Loaded = "0";
        console.error("JS9 display not ready:", displayId);
      }
    }, 250);
  }

  function initJS9() {
    document.querySelectorAll("[data-js9-shell]").forEach(bootJS9Shell);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initJS9, { once: true });
  } else {
    initJS9();
  }
})();
