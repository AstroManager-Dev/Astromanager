(function () {
  function initOpenSeadragon(shell) {
    if (!shell || shell.dataset.osdLoaded === "1") {
      return;
    }
    if (typeof window.OpenSeadragon !== "function") {
      return;
    }

    const viewerId = shell.dataset.osdViewerId || "osd-viewer";
    const imageUrl = shell.dataset.osdImageUrl || "";
    if (!imageUrl) {
      return;
    }

    shell.dataset.osdLoaded = "1";

    const viewer = window.OpenSeadragon({
      id: viewerId,
      prefixUrl: "/static/vendor/openseadragon/images/",
      tileSources: {
        type: "image",
        url: imageUrl,
      },
      showNavigator: false,
      showNavigationControl: false,
      gestureSettingsTouch: {
        pinchToZoom: true,
        flickEnabled: true,
        clickToZoom: false,
        dblClickToZoom: true,
        dragToPan: true,
      },
      gestureSettingsMouse: {
        clickToZoom: false,
        dblClickToZoom: true,
        dragToPan: true,
        scrollToZoom: true,
      },
      minZoomImageRatio: 1,
      maxZoomPixelRatio: 4,
      visibilityRatio: 1,
      constrainDuringPan: true,
      autoHideControls: false,
      immediateRender: true,
      blendTime: 0,
      animationTime: 0.8,
      timeout: 15000,
    });

    shell.querySelectorAll("[data-osd-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        const action = button.dataset.osdAction || "";
        if (action === "zoom-in") {
          viewer.viewport.zoomBy(1.4);
          viewer.viewport.applyConstraints();
          return;
        }
        if (action === "zoom-out") {
          viewer.viewport.zoomBy(0.7);
          viewer.viewport.applyConstraints();
          return;
        }
        if (action === "home") {
          viewer.viewport.goHome();
          return;
        }
        if (action === "full-page") {
          viewer.setFullPage(!viewer.isFullPage());
        }
      });
    });
  }

  function boot() {
    document.querySelectorAll("[data-osd-shell]").forEach(initOpenSeadragon);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
