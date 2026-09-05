/**
 * static/js/playground.js
 * Interactive Live Solver Playground & Code Snippet Copy System
 * Zero-blue color scheme, emerald toast feedback.
 */

(function () {
  "use strict";

  // ── Global Toast Notification ──────────────────────────────────────────────
  window.showToast = function (message, type = "success") {
    let container = document.getElementById("global-toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "global-toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = "toast";
    
    // Icon
    const iconSvg = type === "success" 
      ? '<svg class="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>'
      : '<svg class="w-4 h-4 text-amber-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>';

    toast.innerHTML = `${iconSvg}<span>${message}</span>`;
    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => toast.classList.add("toast-show"));

    // Remove after 2.8s
    setTimeout(() => {
      toast.classList.remove("toast-show");
      setTimeout(() => toast.remove(), 300);
    }, 2800);
  };

  // ── Copy Code Snippet System ───────────────────────────────────────────────
  window.copySnippet = function (targetId, btnElement) {
    const codeBlock = document.getElementById(targetId);
    if (!codeBlock) return;

    const text = codeBlock.innerText.trim();
    navigator.clipboard.writeText(text).then(() => {
      // Visual button feedback
      if (btnElement) {
        const originalHtml = btnElement.innerHTML;
        btnElement.innerHTML = `
          <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
          </svg>
          <span class="text-emerald-400 font-semibold">Copied!</span>
        `;
        setTimeout(() => {
          btnElement.innerHTML = originalHtml;
        }, 2000);
      }
      showToast("Snippet copied to clipboard!");
    }).catch(err => {
      console.error("Clipboard copy failed:", err);
      showToast("Could not copy snippet", "error");
    });
  };

  // ── Multi-Language Tab Switcher ────────────────────────────────────────────
  window.switchCodeTab = function (lang) {
    const tabs = ["curl", "python", "javascript"];
    tabs.forEach(t => {
      const pane = document.getElementById(`snippet-${t}`);
      const btn = document.getElementById(`tab-btn-${t}`);
      if (pane) {
        if (t === lang) {
          pane.classList.remove("hidden");
        } else {
          pane.classList.add("hidden");
        }
      }
      if (btn) {
        if (t === lang) {
          btn.className = "px-3 py-1.5 text-xs font-semibold text-emerald-400 border-b-2 border-emerald-400 transition-colors";
        } else {
          btn.className = "px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors";
        }
      }
    });
  };

  // ── Interactive Live Playground ────────────────────────────────────────────
  let activeChallengeType = "digit";
  let currentPlaygroundSession = null;

  window.setPlaygroundType = function (type) {
    activeChallengeType = type;
    const btnDigit = document.getElementById("pg-tab-digit");
    const btnGrid = document.getElementById("pg-tab-grid");

    if (type === "digit") {
      btnDigit.className = "px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 transition-all";
      btnGrid.className = "px-4 py-2 text-sm font-medium rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-all";
    } else {
      btnGrid.className = "px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 transition-all";
      btnDigit.className = "px-4 py-2 text-sm font-medium rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-all";
    }
    fetchLiveChallenge();
  };

  window.fetchLiveChallenge = async function () {
    const displayArea = document.getElementById("pg-display-area");
    const jsonViewer = document.getElementById("pg-json-viewer");
    const statusText = document.getElementById("pg-status-text");

    if (!displayArea || !jsonViewer) return;

    displayArea.innerHTML = `
      <div class="flex flex-col items-center justify-center h-48 text-zinc-500">
        <svg class="w-6 h-6 animate-spin text-emerald-400 mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span class="text-xs">Generating live challenge from backend...</span>
      </div>
    `;
    if (statusText) statusText.textContent = "Requesting challenge...";

    try {
      const endpoint = activeChallengeType === "digit" ? "/api/captcha-digit" : "/api/captcha-grid";
      const startMs = performance.now();
      const res = await fetch(endpoint);
      const latency = Math.round(performance.now() - startMs);

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      currentPlaygroundSession = data;

      // Update JSON viewer
      jsonViewer.textContent = JSON.stringify(data, null, 2);

      if (statusText) {
        statusText.innerHTML = `<span class="text-emerald-400">● Live 200 OK</span> (${latency}ms)`;
      }

      if (activeChallengeType === "digit") {
        renderDigitPlayground(data);
      } else {
        renderGridPlayground(data);
      }
    } catch (err) {
      console.error("Playground fetch error:", err);
      displayArea.innerHTML = `
        <div class="text-center text-rose-400 p-6 text-sm">
          Failed to fetch challenge: ${err.message}
        </div>
      `;
      if (statusText) statusText.innerHTML = `<span class="text-rose-400">● Error</span>`;
    }
  };

  function renderDigitPlayground(data) {
    const displayArea = document.getElementById("pg-display-area");
    displayArea.innerHTML = `
      <div class="flex flex-col items-center gap-4">
        <div class="p-2 bg-black/60 rounded-xl border border-zinc-800 shadow-inner">
          <img src="${data.captcha_image_url}?t=${Date.now()}" alt="Live Digit CAPTCHA" width="280" height="90" class="rounded">
        </div>
        <div class="flex gap-2 w-full max-w-xs">
          <input type="text" id="pg-digit-input" maxlength="6" placeholder="Solve or simulate" 
            class="flex-1 bg-zinc-900/80 border border-zinc-700 text-white rounded-lg px-3 py-2 text-center font-mono tracking-widest text-sm focus:outline-none focus:border-emerald-500">
          <button onclick="simulateDigitSolve()" class="px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-xs rounded-lg transition-colors flex items-center gap-1">
            ⚡ Solve
          </button>
        </div>
        <div id="pg-solve-result" class="text-xs text-zinc-400 text-center min-h-[1.5rem]"></div>
      </div>
    `;
  }

  function renderGridPlayground(data) {
    const displayArea = document.getElementById("pg-display-area");
    let tilesHtml = data.image_urls.map((url, idx) => `
      <div class="grid-tile relative" data-idx="${idx}" onclick="togglePlaygroundTile(this)">
        <img src="${url}?t=${Date.now()}" alt="Tile ${idx}">
        <div class="tile-check-icon hidden">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
      </div>
    `).join("");

    displayArea.innerHTML = `
      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between text-xs px-1">
          <span class="font-semibold text-emerald-400 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            ${data.instruction}
          </span>
          <button onclick="simulateGridSolve()" class="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500 text-emerald-400 hover:text-zinc-950 border border-emerald-500/40 rounded text-xs font-semibold transition-all flex items-center gap-1">
            ⚡ Auto-Solve AI
          </button>
        </div>
        <div class="grid grid-cols-3 gap-1.5 max-w-[280px] mx-auto">
          ${tilesHtml}
        </div>
        <div id="pg-solve-result" class="text-xs text-zinc-400 text-center min-h-[1.5rem]"></div>
      </div>
    `;
  }

  window.togglePlaygroundTile = function (el) {
    el.classList.toggle("tile-selected");
    const check = el.querySelector(".tile-check-icon");
    if (check) check.classList.toggle("hidden");
  };

  window.simulateDigitSolve = async function () {
    if (!currentPlaygroundSession) return;
    const input = document.getElementById("pg-digit-input");
    const resultEl = document.getElementById("pg-solve-result");
    const jsonViewer = document.getElementById("pg-json-viewer");

    const answer = (input && input.value.trim()) || "123456";
    if (resultEl) resultEl.innerHTML = `<span class="text-zinc-400">Verifying challenge...</span>`;

    try {
      const res = await fetch("/api/verify-digit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentPlaygroundSession.session_id,
          answer: answer
        })
      });
      const data = await res.json();
      if (jsonViewer) jsonViewer.textContent = JSON.stringify(data, null, 2);

      if (data.success) {
        resultEl.innerHTML = `<span class="text-emerald-400 font-bold">✓ Solved Correctly!</span> Ground truth: <code class="text-white">${data.correct_answer}</code>`;
        showToast("AI Agent: Challenge Solved Correctly!");
      } else {
        resultEl.innerHTML = `<span class="text-amber-400 font-semibold">✗ Incorrect Answer.</span> Ground truth answer was: <code class="text-emerald-300 font-mono font-bold">${data.correct_answer}</code>`;
      }
    } catch (err) {
      if (resultEl) resultEl.innerHTML = `<span class="text-rose-400">Error: ${err.message}</span>`;
    }
  };

  window.simulateGridSolve = async function () {
    if (!currentPlaygroundSession) return;
    const resultEl = document.getElementById("pg-solve-result");
    const jsonViewer = document.getElementById("pg-json-viewer");

    const selectedTiles = Array.from(document.querySelectorAll("#pg-display-area .grid-tile.tile-selected"));
    const selectedIndices = selectedTiles.map(t => parseInt(t.dataset.idx, 10));

    if (resultEl) resultEl.innerHTML = `<span class="text-zinc-400">AI Agent evaluating tiles...</span>`;

    try {
      const res = await fetch("/api/verify-grid", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentPlaygroundSession.session_id,
          selected_indices: selectedIndices
        })
      });
      const data = await res.json();
      if (jsonViewer) jsonViewer.textContent = JSON.stringify(data, null, 2);

      if (data.success) {
        resultEl.innerHTML = `<span class="text-emerald-400 font-bold">✓ 100% Tile Match!</span> Correct indices: [${data.correct_indices.join(", ")}]`;
        showToast("AI Agent: Grid Challenge Solved!");
      } else {
        resultEl.innerHTML = `<span class="text-amber-400 font-semibold">Mismatch.</span> True positive tiles were: <code class="text-emerald-300 font-mono font-bold">[${data.correct_indices.join(", ")}]</code>`;
      }
    } catch (err) {
      if (resultEl) resultEl.innerHTML = `<span class="text-rose-400">Error: ${err.message}</span>`;
    }
  };

  // Auto-init on page load if playground element exists
  document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("pg-display-area")) {
      fetchLiveChallenge();
    }
  });
})();
