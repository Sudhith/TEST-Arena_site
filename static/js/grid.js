/**
 * static/js/grid.js
 * Handles the 3×3 image tile selection for the grid CAPTCHA login page.
 *
 * Behaviour:
 *  - Click a tile → toggles selected state (blue border + checkmark overlay)
 *  - Hidden checkboxes track state so form POST sends selected_indices[]
 *  - "↻ New Challenge" button fetches a fresh session via the API
 */

(function () {
  "use strict";

  // ── Tile selection ─────────────────────────────────────────────────────────
  const grid = document.getElementById("captcha-grid");
  if (!grid) return;

  grid.addEventListener("click", function (e) {
    const tile = e.target.closest(".grid-tile");
    if (!tile) return;

    const idx = tile.dataset.index;
    const checkbox = document.getElementById("tile-check-" + idx);
    if (!checkbox) return;

    const selected = !checkbox.checked;
    checkbox.checked = selected;

    // Visual feedback
    if (selected) {
      tile.classList.add("ring-2", "ring-indigo-500", "ring-offset-2", "ring-offset-gray-900");
      tile.querySelector(".tile-check-icon").classList.remove("hidden");
    } else {
      tile.classList.remove("ring-2", "ring-indigo-500", "ring-offset-2", "ring-offset-gray-900");
      tile.querySelector(".tile-check-icon").classList.add("hidden");
    }
  });

  // ── New challenge button ───────────────────────────────────────────────────
  const refreshBtn = document.getElementById("refresh-grid");
  const sessionInput = document.getElementById("session-id");
  const instructionEl = document.getElementById("grid-instruction");

  if (!refreshBtn || !sessionInput) return;

  refreshBtn.addEventListener("click", async function () {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Loading…";

    try {
      const response = await fetch("/api/captcha-grid", {
        method: "GET",
        headers: { Accept: "application/json" },
      });

      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();

      // Update session ID
      sessionInput.value = data.session_id;

      // Update instruction text
      if (instructionEl) instructionEl.textContent = data.instruction;

      // Re-render grid tiles
      _renderTiles(data.image_urls);

    } catch (err) {
      console.error("Failed to refresh grid CAPTCHA:", err);
      alert("Could not load a new challenge. Please reload the page.");
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "↻ New Challenge";
    }
  });

  function _renderTiles(imageUrls) {
    grid.innerHTML = "";
    imageUrls.forEach(function (url, idx) {
      const tile = document.createElement("div");
      tile.className =
        "grid-tile relative cursor-pointer rounded-lg overflow-hidden " +
        "border-2 border-transparent transition-all duration-150 select-none";
      tile.dataset.index = idx;

      const img = document.createElement("img");
      img.src = url + "?t=" + Date.now();
      img.alt = "CAPTCHA tile " + (idx + 1);
      img.className = "w-full h-full object-cover pointer-events-none";
      img.width = 150;
      img.height = 150;

      // Checkmark overlay (hidden by default)
      const icon = document.createElement("div");
      icon.className =
        "tile-check-icon hidden absolute top-1 right-1 " +
        "bg-indigo-600 rounded-full w-5 h-5 flex items-center justify-center";
      icon.innerHTML =
        '<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>' +
        "</svg>";

      // Hidden checkbox
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.name = "selected_indices";
      checkbox.value = idx;
      checkbox.id = "tile-check-" + idx;
      checkbox.className = "hidden";

      tile.appendChild(img);
      tile.appendChild(icon);
      tile.appendChild(checkbox);
      grid.appendChild(tile);
    });
  }
})();
