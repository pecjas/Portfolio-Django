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

  function menuItems(panel) {
    return Array.prototype.slice.call(panel.querySelectorAll("button"));
  }

  function focusItem(panel, index) {
    var items = menuItems(panel);
    if (!items.length) return;

    // Wrap at both ends rather than dead-ending.
    var wrapped = (index + items.length) % items.length;
    items[wrapped].focus();
  }

  function openMenu(menu, focusFirst) {
    var button = menu.querySelector("[data-menu-button]");
    var panel = menu.querySelector("[data-menu-panel]");

    closeAllMenus(menu);
    button.setAttribute("aria-expanded", "true");
    panel.hidden = false;

    if (focusFirst) focusItem(panel, 0);
  }

  function closeMenu(menu, returnFocus) {
    var button = menu.querySelector("[data-menu-button]");

    button.setAttribute("aria-expanded", "false");
    menu.querySelector("[data-menu-panel]").hidden = true;

    if (returnFocus) button.focus();
  }

  function initMenus() {
    var menus = document.querySelectorAll("[data-menu]");
    if (!menus.length) return;

    menus.forEach(function (menu) {
      var button = menu.querySelector("[data-menu-button]");
      var panel = menu.querySelector("[data-menu-panel]");

      button.addEventListener("click", function (event) {
        event.stopPropagation();

        if (button.getAttribute("aria-expanded") === "true") closeMenu(menu, false);
        else openMenu(menu, false);
      });

      // Down-arrow from the trigger opens and lands on the first option.
      button.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;

        event.preventDefault();
        openMenu(menu, false);
        focusItem(panel, event.key === "ArrowDown" ? 0 : -1);
      });

      panel.addEventListener("click", function (event) {
        event.stopPropagation();
      });

      panel.addEventListener("keydown", function (event) {
        var items = menuItems(panel);
        var at = items.indexOf(document.activeElement);

        switch (event.key) {
          case "ArrowDown":
            event.preventDefault();
            focusItem(panel, at + 1);
            break;
          case "ArrowUp":
            event.preventDefault();
            focusItem(panel, at - 1);
            break;
          case "Home":
            event.preventDefault();
            focusItem(panel, 0);
            break;
          case "End":
            event.preventDefault();
            focusItem(panel, items.length - 1);
            break;
          case "Tab":
            // Let focus leave naturally, but do not leave the panel open behind it.
            closeMenu(menu, false);
            break;
          default:
            // Type-ahead: one printable character jumps to the next match.
            if (event.key.length !== 1 || event.altKey || event.ctrlKey || event.metaKey) return;

            var needle = event.key.toLowerCase();
            for (var step = 1; step <= items.length; step++) {
              var candidate = items[(at + step + items.length) % items.length];
              if (candidate.textContent.trim().toLowerCase().indexOf(needle) === 0) {
                event.preventDefault();
                candidate.focus();
                break;
              }
            }
        }
      });
    });

    document.addEventListener("click", function () {
      closeAllMenus(null);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;

      var open = document.querySelector('[data-menu-button][aria-expanded="true"]');
      if (!open) return;

      closeAllMenus(null);
      open.focus();
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

  /* Card summaries are clamped to three lines in CSS. The full text opens in
     a popover rather than expanding in place: unclamping inline pushed every
     card below it down the page, so the thing you were trying to read moved
     while you read it.

     Uses the Popover API, which renders in the top layer -- above every card,
     immune to ancestor overflow and stacking contexts. Where that is missing,
     the button falls back to expanding in place, which is worse but still
     gets you the text. */
  var POPOVER_SUPPORTED =
    typeof HTMLElement !== "undefined" &&
    typeof HTMLElement.prototype.showPopover === "function";

  var GAP = 10;

  /* Positioning only. Every way of opening a popover -- the button's
     popovertarget, a hover, anything programmatic -- routes through its own
     toggle event, so this runs from there rather than from each trigger.
     Positioning from the click handler did not work: an invoker opens the
     popover after event dispatch, so at click time it was still closed. */
  /* The area the popover must not cover: the summary, plus the Show more
     button when it is on screen. Anchoring to the summary alone put the
     popover straight over the button on touch, where the button is the only
     way to close it again. */
  function anchorRect(summary, button) {
    var box = summary.getBoundingClientRect();

    if (!button || button.hidden ||
        window.getComputedStyle(button).display === "none") {
      return box;
    }

    var extra = button.getBoundingClientRect();

    return {
      left: Math.min(box.left, extra.left),
      right: Math.max(box.right, extra.right),
      top: Math.min(box.top, extra.top),
      bottom: Math.max(box.bottom, extra.bottom),
      width: Math.max(box.right, extra.right) - Math.min(box.left, extra.left)
    };
  }

  function positionPopover(popover, box) {
    var width = popover.offsetWidth;
    var height = popover.offsetHeight;

    var left = box.left + box.width / 2 - width / 2;
    left = Math.max(GAP, Math.min(left, window.innerWidth - width - GAP));

    var top = box.bottom + GAP;
    if (top + height > window.innerHeight - GAP) {
      var above = box.top - height - GAP;
      if (above >= GAP) top = above;
    }

    // Clamp last, and against both edges. Checking only the top edge let an
    // anchor that was itself below the fold place the popover off-screen --
    // "above" an off-screen element is still off-screen.
    top = Math.min(top, window.innerHeight - height - GAP);
    top = Math.max(GAP, top);

    popover.style.left = Math.round(left) + "px";
    popover.style.top = Math.round(top) + "px";
  }

  function initSummaries() {
    var cards = document.querySelectorAll(".project-card");
    if (!cards.length) return;

    var hoverable = window.matchMedia("(hover: hover) and (pointer: fine)");
    var counter = 0;

    /* Only one auto popover can be open at a time, so one pair of globals is
       enough, and one scroll listener rather than one per card. */
    var openPopover = null;
    var openAnchor = null;
    var frame = 0;

    function follow() {
      frame = 0;
      if (!openPopover || !openAnchor) return;

      var box = anchorRect(openAnchor.summary, openAnchor.button);

      // Scrolled past the card it belongs to: close rather than leave it
      // clamped to the viewport edge, detached from anything.
      if (box.bottom < 0 || box.top > window.innerHeight) {
        openPopover.hidePopover();
        return;
      }

      positionPopover(openPopover, box);
    }

    function schedule() {
      /* Cancel and re-request rather than guarding with a boolean. A tab that
         is hidden mid-scroll never runs the frame, which would leave a "queued"
         flag latched true and stop every later scroll from scheduling
         anything. Replacing the handle cannot latch. */
      if (frame) window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(follow);
    }

    /* Scrolling used to close the popover. That left it unopenable: the card
       moves under a stationary cursor without firing mouseenter again, so
       nothing reopened it until you left the card and came back. It now
       follows the anchor instead. */
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && openPopover) openPopover.hidePopover();
    });

    cards.forEach(function (card) {
      var summary = card.querySelector(".project-card__summary");
      var title = card.querySelector(".card__title");
      if (!summary) return;

      var button = document.createElement("button");
      button.type = "button";
      button.className = "card__more";
      button.hidden = true;
      button.setAttribute("aria-expanded", "false");
      button.textContent = "Show more";
      summary.insertAdjacentElement("afterend", button);

      var popover = null;
      var pointerInside = false;
      var dismissed = false;

      if (POPOVER_SUPPORTED) {
        counter += 1;
        popover = document.createElement("div");
        popover.className = "summary-popover";
        popover.id = "summary-popover-" + counter;
        /* Manual, not auto: an auto popover light-dismisses on any outside
           click, so clicking the card you were reading closed it. That also
           means closing the previous one and handling Escape are ours to do,
           both below. */
        popover.setAttribute("popover", "manual");

        if (title) {
          var heading = document.createElement("span");
          heading.className = "summary-popover__title";
          heading.textContent = title.textContent.trim();
          popover.appendChild(heading);
        }

        var body = document.createElement("p");
        body.textContent = summary.textContent.trim();
        popover.appendChild(body);

        document.body.appendChild(popover);

        // The browser wires up toggling and the implicit relationship.
        button.setAttribute("popovertarget", popover.id);

        // Hidden between being shown and being placed, so it never paints a
        // frame in the default centred position first.
        popover.addEventListener("beforetoggle", function (event) {
          if (event.newState === "open") popover.style.visibility = "hidden";
        });

        popover.addEventListener("toggle", function (event) {
          var isOpen = event.newState === "open";

          button.setAttribute("aria-expanded", String(isOpen));
          button.textContent = isOpen ? "Show less" : "Show more";

          if (isOpen) {
            if (openPopover && openPopover !== popover) openPopover.hidePopover();

            positionPopover(popover, anchorRect(summary, button));
            popover.style.visibility = "";
            openPopover = popover;
            openAnchor = { summary: summary, button: button };
          } else {
            if (openPopover === popover) {
              openPopover = null;
              openAnchor = null;
            }

            // Closed by Escape or the button while the pointer is still over
            // the card: do not immediately reopen it from under them.
            if (pointerInside) dismissed = true;
          }
        });

        var open = function () {
          if (!button.hidden && !popover.matches(":popover-open")) {
            popover.showPopover();
          }
        };
        var close = function () {
          if (popover.matches(":popover-open")) popover.hidePopover();
        };

        /* Bound to the summary and nothing else. The popover shows the three
           clamped lines in full, so those three lines are the only thing that
           should summon it -- not the tags, not the languages, not the link
           row, and not the popover itself. */
        function reveal() {
          if (!hoverable.matches || dismissed) return;

          if (popover.matches(":popover-open")) {
            // Already open: make sure it is still where the card is. Scroll
            // events do not fire in a tab the browser has stopped rendering,
            // so the position can be stale by the time the pointer moves.
            follow();
          } else {
            open();
          }
        }

        summary.addEventListener("mouseenter", function () {
          pointerInside = true;
          dismissed = false;
          reveal();
        });

        // The safety net for the stationary-cursor case: after a scroll the
        // pointer can already be over a summary it never "entered".
        summary.addEventListener("mousemove", reveal);

        summary.addEventListener("mouseleave", function () {
          pointerInside = false;
          dismissed = false;
          if (hoverable.matches) close();
        });

        /* No focus trigger. Tabbing to the card's link -- or clicking it,
           which focuses it -- opened the description, which is one of the
           "any other time" cases. The clamp is visual only, so the full text
           is still read by assistive tech straight from the card, and the
           project page carries it in full. */

      } else {
        button.addEventListener("click", function () {
          var expanded = summary.classList.toggle("is-expanded");
          button.setAttribute("aria-expanded", String(expanded));
          button.textContent = expanded ? "Show less" : "Show more";
        });
      }

      function measure() {
        if (summary.classList.contains("is-expanded")) return;

        var clipped = summary.scrollHeight > summary.clientHeight + 1;
        if (clipped === !button.hidden) return;

        button.hidden = !clipped;
        summary.classList.toggle("is-clipped", clipped);
      }

      measure();

      if (window.ResizeObserver) {
        new window.ResizeObserver(measure).observe(summary);
      } else {
        window.addEventListener("resize", measure);
      }
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
    initSummaries();
    markCurrentPage();
  });
})();
