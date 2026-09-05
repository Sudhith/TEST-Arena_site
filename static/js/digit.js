/**
 * static/js/digit.js
 * Handles the "↻ Refresh CAPTCHA" button on the digit login page.
 * Fetches a new session_id from the API and updates the image src + hidden field.
 */

(function () {
  "use strict";

  const refreshBtn = document.getElementById("refresh-captcha");
  const captchaImg = document.getElementById("captcha-img");
  const sessionInput = document.getElementById("session-id");

  if (!refreshBtn || !captchaImg || !sessionInput) return;

  refreshBtn.addEventListener("click", async function () {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Loading…";

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
    } catch (err) {
      console.error("Failed to refresh CAPTCHA:", err);
      alert("Could not refresh CAPTCHA. Please reload the page.");
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "↻ Refresh";
    }
  });
})();
