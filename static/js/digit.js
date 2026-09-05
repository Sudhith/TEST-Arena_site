/**
 * static/js/digit.js
 * Handles async refresh for the 6-digit numeric CAPTCHA.
 * Zero-blue color scheme, emerald toast feedback.
 */

(function () {
  "use strict";

  const refreshBtn = document.getElementById("refresh-captcha");
  const captchaImg = document.getElementById("captcha-img");
  const sessionInput = document.getElementById("session-id");

  if (!refreshBtn || !captchaImg || !sessionInput) return;

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
      const response = await fetch("/api/captcha-digit", {
        method: "GET",
        headers: { Accept: "application/json" },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Update hidden field and image without page reload
      sessionInput.value = data.session_id;
      captchaImg.src = data.captcha_image_url + "?t=" + Date.now(); // cache-bust

      if (window.showToast) {
        window.showToast("New 6-digit CAPTCHA generated");
      }
    } catch (err) {
      console.error("Failed to refresh CAPTCHA:", err);
      if (window.showToast) {
        window.showToast("Could not refresh CAPTCHA", "error");
      } else {
        alert("Could not refresh CAPTCHA. Please reload the page.");
      }
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = `↻ Refresh`;
    }
  });
})();
