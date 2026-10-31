/**
 * ToolNest API Client: Cold-Start Mitigation & Error Handling
 * Pre-warms free Render backend on tool pages and retries safely.
 */
const ToolNestAPI = (function () {
  // Reads the API base URL injected into window.TOOLNEST_CONFIG or defaults to relative/configured
  function getApiBaseUrl() {
    if (window.TOOLNEST_CONFIG && window.TOOLNEST_CONFIG.apiBaseUrl) {
      return window.TOOLNEST_CONFIG.apiBaseUrl.replace(/\/+$/, '');
    }
    return '';
  }

  let isApiAwake = false;
  let healthCheckInProgress = false;

  async function prewarmBackend(onStatusChange) {
    if (isApiAwake || healthCheckInProgress) return;
    healthCheckInProgress = true;

    const baseUrl = getApiBaseUrl();
    const healthUrl = `${baseUrl}/health`;
    const banner = document.getElementById('api-status-banner');
    const submitBtns = document.querySelectorAll('.server-tool-btn');

    function updateUI(status, message) {
      if (banner) {
        if (message) {
          banner.textContent = message;
          banner.classList.add('active');
        } else {
          banner.classList.remove('active');
        }
      }
      submitBtns.forEach(btn => {
        if (status === 'ready') {
          btn.removeAttribute('disabled');
        } else {
          btn.setAttribute('disabled', 'disabled');
        }
      });
      if (onStatusChange) onStatusChange(status, message);
    }

    const startTime = Date.now();
    const MAX_WAIT_MS = 90000; // 90 seconds max retry
    let delayTimer = null;

    // Show initial waking message after 5 seconds of silence
    delayTimer = setTimeout(() => {
      if (!isApiAwake) {
        updateUI('waking', 'Starting the processing server, this can take up to a minute...');
      }
    }, 5000);

    while (Date.now() - startTime < MAX_WAIT_MS) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);

        const res = await fetch(healthUrl, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (res.ok) {
          clearTimeout(delayTimer);
          isApiAwake = true;
          healthCheckInProgress = false;
          updateUI('ready', null);
          return true;
        }
      } catch (err) {
        // Backend is still waking up, wait 5s and retry
      }
      await new Promise(r => setTimeout(r, 5000));
    }

    clearTimeout(delayTimer);
    healthCheckInProgress = false;
    updateUI('error', 'Server is taking longer than usual to wake up. Please refresh or try again in a moment.');
    return false;
  }

  async function request(endpoint, options = {}) {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, options);

      // Handle successful binary output (PDF/Images/ZIP)
      const contentType = response.headers.get('content-type') || '';
      if (response.ok) {
        if (contentType.includes('application/json')) {
          return await response.json();
        }
        return await response.blob();
      }

      // Handle standard error contract { "code": "...", "message": "..." }
      if (contentType.includes('application/json')) {
        const errJson = await response.json();
        throw new Error(errJson.message || 'Operation failed');
      }

      throw new Error(`Request failed with status ${response.status}`);
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('This file took too long to process. Try a smaller file');
      }
      throw err;
    }
  }

  return {
    prewarmBackend,
    request,
    isAwake: () => isApiAwake,
  };
})();
