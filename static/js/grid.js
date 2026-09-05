/**
 * static/js/grid.js
 * Handles the 3x3 image tile selection for the grid CAPTCHA login page.
 * Color Palette: Electric Emerald & Obsidian Black (Strictly Zero Blue)
 */

(function () {
  "use strict";

  const grid = document.getElementById("captcha-grid");
  if (!grid) return;

  // ── Tile click toggle ──────────────────────────────────────────────────────
  grid.addEventListener("click", function (e) {
    const tile = e.target.closest(".grid-tile");
    if (!tile) return;

    const idx = tile.dataset.index;
    const checkbox = document.getElementById("tile-check-" + idx);
    if (!checkbox) return;

    const selected = !checkbox.checked;
    checkbox.checked = selected;

    // Visual feedback: emerald border + glow + checkmark badge
    if (selected) {
      tile.classList.add("tile-selected");
      const icon = tile.querySelector(".tile-check-icon");
      if (icon) icon.classList.remove("hidden");
    } else {
      tile.classList.remove("tile-selected");
      const icon = tile.querySelector(".tile-check-icon");
      if (icon) icon.classList.add("hidden");
    }
  });

  // ── Async refresh challenge ────────────────────────────────────────────────
  const refreshBtn = document.getElementById("refresh-grid");
  const sessionInput = document.getElementById("session-id");
  const instructionEl = document.getElementById("grid-instruction");

  if (!refreshBtn || !sessionInput) return;

  refreshBtn.addEventListener("click", async function () {
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = `
      <svg class="w-3.5 h-3.5 animate-spin inline-block text-emerald-400" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
      <span>Loading...</span>
    `;

    try {
      const response = await fetch("/api/captcha-grid", {
        method: "GET",
        headers: { Accept: "application/json" },
      });

      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();

      sessionInput.value = data.session_id;

      if (instructionEl) {
        instructionEl.textContent = data.instruction;
      }

      _renderTiles(data.image_urls);

      if (window.showToast) {
        window.showToast("New image challenge loaded");
      }
    } catch (err) {
      console.error("Failed to refresh grid CAPTCHA:", err);
      if (window.showToast) {
        window.showToast("Failed to refresh challenge", "error");
      } else {
        alert("Could not load a new challenge. Please reload the page.");
      }
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = `↻ New Challenge`;
    }
  });

  function _renderTiles(imageUrls) {
    grid.innerHTML = "";
    imageUrls.forEach(function (url, idx) {
      const tile = document.createElement("div");
      tile.className = "grid-tile";
      tile.dataset.index = idx;

      const img = document.createElement("img");
      img.src = url + "?t=" + Date.now();
      img.alt = "CAPTCHA tile " + (idx + 1);
      img.width = 150;
      img.height = 150;

      const icon = document.createElement("div");
      icon.className = "tile-check-icon hidden";
      icon.innerHTML = `
        <svg class="w-3.5 h-3.5 text-zinc-950 font-bold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
        </svg>
      `;

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
