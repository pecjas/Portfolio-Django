/* Project filtering. Replaces the jQuery implementation.

   Semantics: OR within a category, AND across categories. Selecting Python and
   Mumps shows projects using either, which is what a faceted filter is expected
   to do; the previous version intersected them and narrowed to projects using
   both. */

(function () {
  "use strict";

  /* Escape hatch: set false to stop the filters touching the History API at
     all. Filters still apply and shared links still load; the address bar just
     stops tracking them. See the reconciler below for why it should not be
     needed. */
  var SYNC_URL_TO_FILTERS = true;

  /* How often the reconciler checks whether the URL has fallen behind. */
  var URL_RECONCILE_MS = 600;

  /* Which query parameter each category reads and writes. Categories
     themselves are discovered from the DOM at init, in the order the template
     renders their menus, so a group the server chose not to render simply does
     not participate — that is how the capability filter stays absent until
     projects claim one, with no flag to keep in sync here. */
  var CATEGORY_PARAMS = {
    "data-filter-capability": "work",
    "data-filter-lang": "lang",
    "data-filter-personal-status": "kind"
  };

  var CATEGORIES = [];

  var cards = [];
  var selected = {};
  var elements = {};

  /* category + "|" + value -> the label a human reads, e.g. "C#" for C_Sharp.
     Read off the menu buttons at init so the display names stay in one place,
     the template. */
  var labels = {};

  function labelFor(category, value) {
    return labels[category + "|" + value] || value;
  }

  function selectedIn(category) {
    return selected[category] || [];
  }

  function cardMatches(card, category) {
    var chosen = selectedIn(category);
    if (!chosen.length) return true;

    var values = (card.getAttribute(category) || "").split(" ");

    return chosen.some(function (value) {
      return values.indexOf(value) !== -1;
    });
  }

  function visibleCards() {
    return cards.filter(function (card) {
      return CATEGORIES.every(function (category) {
        return cardMatches(card, category);
      });
    });
  }

  function render() {
    var shown = visibleCards();

    cards.forEach(function (card) {
      card.hidden = shown.indexOf(card) === -1;
    });

    if (elements.count) {
      elements.count.textContent = shown.length === cards.length
        ? "Showing all " + cards.length + " projects"
        : "Showing " + shown.length + " of " + cards.length + " projects";
    }

    /* A section whose cards have all been filtered out must take its heading
       with it, or "Selected work" sits above nothing. */
    document.querySelectorAll("[data-work-section]").forEach(function (section) {
      var inSection = section.querySelectorAll("[data-filter-lang]");
      section.hidden = !Array.prototype.some.call(inSection, function (card) {
        return !card.hidden;
      });
    });

    if (elements.empty) elements.empty.hidden = shown.length !== 0;

    if (elements.clear) {
      elements.clear.hidden = CATEGORIES.every(function (category) {
        return selectedIn(category).length === 0;
      });
    }

    document.querySelectorAll("[data-filter-value]").forEach(function (button) {
      var category = button.dataset.filterCategory;
      var isOn = selectedIn(category).indexOf(button.dataset.filterValue) !== -1;
      button.setAttribute("aria-pressed", String(isOn));
    });

    renderChips();
  }

  function renderChips() {
    if (!elements.chips) return;

    // Everything after the label is a chip from the previous render.
    while (elements.chips.lastElementChild && elements.chips.lastElementChild.classList.contains("chip")) {
      elements.chips.removeChild(elements.chips.lastElementChild);
    }

    var any = false;

    CATEGORIES.forEach(function (category) {
      selectedIn(category).forEach(function (value) {
        any = true;
        elements.chips.appendChild(buildChip(category, value));
      });
    });

    elements.chips.hidden = !any;
  }

  function buildChip(category, value) {
    var label = labelFor(category, value);

    var chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.setAttribute("aria-label", "Remove filter: " + label);
    chip.appendChild(document.createTextNode(label));

    var icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("class", "icon");
    icon.setAttribute("aria-hidden", "true");

    var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "#i-close");
    icon.appendChild(use);
    chip.appendChild(icon);

    chip.addEventListener("click", function () {
      var chips = Array.prototype.slice.call(elements.chips.querySelectorAll(".chip"));
      var position = chips.indexOf(chip);

      toggle(category, value);

      // Keep focus in the row rather than dropping it to <body>: the chip that
      // took this one's place, or the clear-all button once the row is empty.
      var remaining = elements.chips.querySelectorAll(".chip");

      if (remaining.length) {
        remaining[Math.min(position, remaining.length - 1)].focus();
      } else if (elements.clear && !elements.clear.hidden) {
        elements.clear.focus();
      }
    });

    return chip;
  }

  function toggle(category, value) {
    var chosen = selectedIn(category);
    var at = chosen.indexOf(value);

    if (at === -1) {
      chosen.push(value);
    } else {
      chosen.splice(at, 1);
    }

    selected[category] = chosen;
    render();
    syncUrl();
  }

  function clearAll() {
    CATEGORIES.forEach(function (category) {
      selected[category] = [];
    });
    render();
    syncUrl();
  }

  /* Filter state lives in the URL so a filtered view can be shared or reloaded.

     The write deliberately does not happen in the click's task, nor in a timer
     started from it. Chrome's soft-navigation heuristics flag one trusted
     interaction that both changes the URL via the History API and mutates the
     DOM, and that interaction context propagates through chained timers — so a
     debounce scheduled from the handler is still attributed to the click.
     DevTools' live performance metrics instrument that path and throw
     "Cannot read properties of undefined (reading 'startTime')" on it.
     Confirmed by bisection: errors with the write on the click path, none
     without it.

     So a click only raises a flag. A reconciler rooted at page load — not a
     descendant of any interaction — notices the flag and writes the URL. Same
     address bar, no interaction for the heuristic to attribute it to. */

  var urlDirty = false;

  function currentQuery() {
    var params = new URLSearchParams();

    CATEGORIES.forEach(function (category) {
      var chosen = selectedIn(category);
      if (chosen.length) params.set(CATEGORY_PARAMS[category], chosen.join(","));
    });

    return params.toString();
  }

  function writeUrl() {
    if (!SYNC_URL_TO_FILTERS) return;

    var query = currentQuery();
    var next = query ? "?" + query : window.location.pathname;

    if (next === window.location.search || (!query && !window.location.search)) return;

    history.replaceState(null, "", next);
  }

  function syncUrl() {
    urlDirty = true;
  }

  function startUrlReconciler() {
    if (!SYNC_URL_TO_FILTERS) return;

    // Rooted here, at load — never inside a click handler.
    window.setInterval(function () {
      if (!urlDirty) return;

      urlDirty = false;
      writeUrl();
    }, URL_RECONCILE_MS);
  }

  function readUrl() {
    var params = SYNC_URL_TO_FILTERS
      ? new URLSearchParams(window.location.search)
      : new URLSearchParams();

    CATEGORIES.forEach(function (category) {
      var raw = params.get(CATEGORY_PARAMS[category]) || "";
      selected[category] = raw.split(",").filter(Boolean);
    });
  }

  function init() {
    var container = document.getElementById("cardContainer");
    if (!container) return;

    /* Menu order is the template's call, and the template leads with the
       primary axis. Reading it here keeps that decision in one place. */
    document.querySelectorAll("[data-filter-value]").forEach(function (button) {
      var category = button.dataset.filterCategory;
      if (CATEGORIES.indexOf(category) === -1) CATEGORIES.push(category);
    });

    cards = Array.prototype.slice.call(container.querySelectorAll("[data-filter-lang]"));
    elements.count = document.getElementById("filter-count");
    elements.empty = document.getElementById("filter-empty");
    elements.clear = document.getElementById("filter-clear");
    elements.chips = document.getElementById("filter-chips");

    readUrl();

    document.querySelectorAll("[data-filter-value]").forEach(function (button) {
      /* Prefer the explicit label: the button's text now also contains a
         result count, and a chip reading "Systems Integration 5" is wrong. */
      labels[button.dataset.filterCategory + "|" + button.dataset.filterValue] =
        button.dataset.filterLabel || button.textContent.trim();

      button.addEventListener("click", function () {
        toggle(button.dataset.filterCategory, button.dataset.filterValue);
      });
    });

    if (elements.clear) elements.clear.addEventListener("click", clearAll);

    startUrlReconciler();
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
