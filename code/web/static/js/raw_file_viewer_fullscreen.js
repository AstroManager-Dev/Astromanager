(function () {
  function openOverlay(button) {
    const overlay = document.getElementById("raw-fullscreen-overlay");
    const stage = document.getElementById("raw-fullscreen-stage");
    const image = document.getElementById("raw-fullscreen-image");
    const osd = document.getElementById("raw-fullscreen-osd");
    if (!overlay || !stage || !image || !osd || !button) return;

    const url = button.dataset.imageUrl || "";
    const kind = button.dataset.viewerKind || "image";
    if (!url) return;

    document.body.classList.add("raw-fullscreen-open");
    overlay.hidden = false;
    image.hidden = true;
    osd.hidden = true;
    stage.dataset.viewerKind = kind;

    if (window.rawFullscreenViewer && typeof window.rawFullscreenViewer.destroy === "function") {
      window.rawFullscreenViewer.destroy();
      window.rawFullscreenViewer = null;
    }

    if (kind === "fits" && window.OpenSeadragon) {
      osd.hidden = false;
      window.rawFullscreenViewer = window.OpenSeadragon({
        element: osd,
        prefixUrl: "/static/vendor/openseadragon/images/",
        tileSources: {
          type: "image",
          url: url
        },
        showNavigationControl: false,
        gestureSettingsTouch: { pinchToZoom: true, flickEnabled: true, dblClickToZoom: true },
        maxZoomPixelRatio: 4,
      });
      return;
    }

    image.src = url;
    image.hidden = false;
  }

  function closeOverlay() {
    const overlay = document.getElementById("raw-fullscreen-overlay");
    const image = document.getElementById("raw-fullscreen-image");
    const osd = document.getElementById("raw-fullscreen-osd");
    if (window.rawFullscreenViewer && typeof window.rawFullscreenViewer.destroy === "function") {
      window.rawFullscreenViewer.destroy();
      window.rawFullscreenViewer = null;
    }
    if (image) image.src = "";
    if (osd) osd.innerHTML = "";
    if (overlay) overlay.hidden = true;
    document.body.classList.remove("raw-fullscreen-open");
  }

  document.addEventListener("click", function (event) {
    const openButton = event.target.closest("[data-open-fullscreen]");
    if (openButton) {
      event.preventDefault();
      openOverlay(openButton);
      return;
    }
    if (event.target.closest("[data-close-fullscreen]")) {
      event.preventDefault();
      closeOverlay();
      return;
    }
    const overlay = document.getElementById("raw-fullscreen-overlay");
    if (overlay && !overlay.hidden && event.target === overlay) {
      closeOverlay();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeOverlay();
  });
})();
