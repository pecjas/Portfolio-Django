/* Site behaviour. Replaces Materialize's JS and jQuery.
   Everything here is progressive: the accordion is a native <details>, the
   nav is usable as links before this runs, and project cards are plain
   anchors. This file adds the drawer, the filter menus, toasts and the
   image lightbox. */

(function () {
  "use strict";

  /* ---------------------------------------------------------------- drawer */

  function initDrawer() {
    var dialog = document.getElementById("nav-drawer");
    var openBtn = document.querySelector("[data-drawer-open]");
    if (!dialog || !openBtn || typeof dialog.showModal !== "function") return;

    openBtn.addEventListener("click", function () {
      dialog.showModal();
    });

    dialog.addEventListener("click", function (event) {
      if (event.target.closest("[data-drawer-close]")) {
        dialog.close();
        return;
      }
      // A click on the dialog element itself is a click on the backdrop.
      if (event.target === dialog) dialog.close();
    });

    // Return focus to the trigger so keyboard users do not land at the top.
    dialog.addEventListener("close", function () {
      openBtn.focus();
    });
  }

  /* ----------------------------------------------------------------- menus */

  function closeAllMenus(except) {
    document.querySelectorAll("[data-menu]").forEach(function (menu) {
      if (menu === except) return;
      menu.querySelector("[data-menu-button]").setAttribute("aria-expanded", "false");
      menu.querySelector("[data-menu-panel]").hidden = true;
    });
  }

  function initMenus() {
    var menus = document.querySelectorAll("[data-menu]");
    if (!menus.length) return;

    menus.forEach(function (menu) {
      var button = menu.querySelector("[data-menu-button]");
      var panel = menu.querySelector("[data-menu-panel]");

      button.addEventListener("click", function (event) {
        event.stopPropagation();
        var isOpen = button.getAttribute("aria-expanded") === "true";
        closeAllMenus(menu);
        button.setAttribute("aria-expanded", String(!isOpen));
        panel.hidden = isOpen;
      });

      panel.addEventListener("click", function (event) {
        event.stopPropagation();
      });
    });

    document.addEventListener("click", function () {
      closeAllMenus(null);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      var open = document.querySelector('[data-menu-button][aria-expanded="true"]');
      closeAllMenus(null);
      if (open) open.focus();
    });
  }

  /* ---------------------------------------------------------------- toasts */

  function initToasts() {
    var queued = document.querySelectorAll("[data-toast]");
    if (!queued.length) return;

    var region = document.createElement("div");
    region.className = "toasts";
    region.setAttribute("role", "status");
    region.setAttribute("aria-live", "polite");
    document.body.appendChild(region);

    queued.forEach(function (node) {
      var toast = document.createElement("div");
      toast.className = "toast toast--" + (node.dataset.toast || "info");
      toast.textContent = node.textContent.trim();
      region.appendChild(toast);

      var life = Number(node.dataset.toastLife || 5000);
      setTimeout(function () {
        toast.remove();
        if (!region.children.length) region.remove();
      }, life);
    });
  }

  /* -------------------------------------------------------------- lightbox */

  function initLightbox() {
    var zoomable = document.querySelectorAll(".zoomable");
    if (!zoomable.length) return;

    var dialog = document.createElement("dialog");
    dialog.className = "lightbox";
    if (typeof dialog.showModal !== "function") return;

    var img = document.createElement("img");
    var closeLabel = document.createElement("button");
    closeLabel.className = "sr-only";
    closeLabel.textContent = "Close image";

    dialog.appendChild(closeLabel);
    dialog.appendChild(img);
    document.body.appendChild(dialog);

    zoomable.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        img.src = thumb.currentSrc || thumb.src;
        img.alt = thumb.alt;
        dialog.showModal();
      });
    });

    dialog.addEventListener("click", function () {
      dialog.close();
    });
  }

  /* ----------------------------------------------------------------- theme */

  /* Three states rather than two: without "system" there is no way back to
     following the OS once a choice has been made. */
  var THEME_ORDER = ["system", "light", "dark"];

  var THEME_UI = {
    system: { icon: "#i-auto", name: "System" },
    light: { icon: "#i-sun", name: "Light" },
    dark: { icon: "#i-moon", name: "Dark" }
  };

  function readTheme() {
    try {
      var saved = localStorage.getItem("theme");
      return saved === "light" || saved === "dark" ? saved : "system";
    } catch (e) {
      return "system";
    }
  }

  function saveTheme(mode) {
    try {
      if (mode === "system") localStorage.removeItem("theme");
      else localStorage.setItem("theme", mode);
    } catch (e) { /* storage blocked; the choice just will not persist */ }
  }

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function effectiveScheme(mode) {
    if (mode === "system") return systemPrefersDark() ? "dark" : "light";
    return mode;
  }

  function applyTheme(mode, button) {
    if (mode === "system") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", mode);
    }

    // Keep the mobile browser chrome in step with the page.
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", effectiveScheme(mode) === "dark" ? "#17101f" : "#44318D");

    if (!button) return;

    var next = THEME_ORDER[(THEME_ORDER.indexOf(mode) + 1) % THEME_ORDER.length];

    button.querySelector("[data-theme-icon] use").setAttribute("href", THEME_UI[mode].icon);
    button.setAttribute("aria-label", "Theme: " + THEME_UI[mode].name + ". Switch to " + THEME_UI[next].name + ".");
    button.setAttribute("title", "Theme: " + THEME_UI[mode].name);
  }

  function initTheme() {
    var button = document.querySelector("[data-theme-toggle]");
    if (!button) return;

    var mode = readTheme();

    // Only revealed once it is wired up, so it is never a dead control.
    button.hidden = false;
    applyTheme(mode, button);

    button.addEventListener("click", function () {
      mode = THEME_ORDER[(THEME_ORDER.indexOf(mode) + 1) % THEME_ORDER.length];
      saveTheme(mode);
      applyTheme(mode, button);
    });

    // While following the OS, track it live rather than only on reload.
    if (window.matchMedia) {
      var query = window.matchMedia("(prefers-color-scheme: dark)");
      var onChange = function () {
        if (mode === "system") applyTheme(mode, button);
      };

      if (query.addEventListener) query.addEventListener("change", onChange);
      else if (query.addListener) query.addListener(onChange);
    }
  }

  /* ------------------------------------------------------ current nav item */

  function markCurrentPage() {
    var here = window.location.pathname;

    document.querySelectorAll("[data-nav-link]").forEach(function (link) {
      var target = link.getAttribute("href");
      var isCurrent = target === "/" ? here === "/" : here.indexOf(target) === 0;
      if (isCurrent) link.setAttribute("aria-current", "page");
    });
  }

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    initTheme();
    initDrawer();
    initMenus();
    initToasts();
    initLightbox();
    markCurrentPage();
  });
})();
