// ShieldAI Content Script — Message Scanner & Threat Badging
let isEnabled = true;
const pendingBatch = [];
let batchTimeout = null;
const BATCH_INTERVAL_MS = 250;
const MAX_BATCH_SIZE = 30;

// Initialize state from background service worker
if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
  try {
    chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response) => {
      if (response && response.isEnabled !== undefined) {
        isEnabled = response.isEnabled;
      }
    });
  } catch (e) {
    // Context invalidated or extension reloaded
  }
}

// React to state changes toggled in popup
if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.onChanged) {
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.isEnabled !== undefined) {
      isEnabled = changes.isEnabled.newValue;
      if (!isEnabled) {
        // Hide badges when toggled off
        document.querySelectorAll('.shieldai-badge').forEach(b => b.style.display = 'none');
      } else {
        document.querySelectorAll('.shieldai-badge').forEach(b => b.style.display = 'inline-flex');
        debouncedScanDOM();
      }
    }
  });
}

// Debounce helper
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Select message containers across Gmail, WhatsApp Web, and local test harness
function getMessageSelector() {
  const hostname = window.location.hostname;
  if (hostname.includes('mail.google.com')) {
    return '.a3s.aiL, div[role="listitem"] .a3s';
  } else if (hostname.includes('web.whatsapp.com')) {
    return 'div.message-in, div.message-out, span.selectable-text';
  }
  // Generic test harness and other web messengers
  return '.chat-message, .message-content, .msg-text, [data-message], .message-bubble, .message-body';
}

// Check an element and queue it for batch scanning
function queueElementForScan(el) {
  if (!isEnabled) return;
  if (!el || el.getAttribute('data-shieldai-checked') === 'true') return;

  // Mark immediately to guarantee no redundant scans
  el.setAttribute('data-shieldai-checked', 'true');

  let text = (el.innerText || el.textContent || '').trim();
  // Filter: skip very short (< 5 chars) or very long (> 2000 chars)
  if (!text || text.length < 5 || text.length > 2000) {
    return;
  }

  pendingBatch.push({ element: el, text: text });

  if (pendingBatch.length >= MAX_BATCH_SIZE) {
    flushBatch();
  } else if (!batchTimeout) {
    batchTimeout = setTimeout(flushBatch, BATCH_INTERVAL_MS);
  }
}

// Flush queued elements as a batch to the background service worker
function flushBatch() {
  if (batchTimeout) {
    clearTimeout(batchTimeout);
    batchTimeout = null;
  }

  if (pendingBatch.length === 0 || !isEnabled) return;

  const currentBatch = pendingBatch.splice(0, MAX_BATCH_SIZE);
  const texts = currentBatch.map(item => item.text);

  if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendMessage) {
    return;
  }

  try {
    // Content script sends batch to background service worker (NEVER calls localhost directly)
    chrome.runtime.sendMessage({ type: 'CHECK_BATCH', texts: texts }, (response) => {
      if (chrome.runtime.lastError) {
        // Backend or extension connection error: handle silently without breaking page
        console.debug('[ShieldAI] Batch runtime notice:', chrome.runtime.lastError.message);
        return;
      }

      if (!response || response.status !== 'success' || !Array.isArray(response.results)) {
        // Backend offline or error: gracefully do nothing
        return;
      }

      const results = response.results;
      currentBatch.forEach((item, idx) => {
        const res = results[idx];
        if (res && !res.error) {
          injectBadge(item.element, res);
        }
      });
    });
  } catch (err) {
    // Ignore runtime disconnection errors gracefully
    console.debug('[ShieldAI] Extension communication error:', err);
  }
}

// Inject colour-coded badge (Amber, Orange, Red) with explanatory tooltip
function injectBadge(element, result) {
  if (!element || element.querySelector('.shieldai-badge')) return;

  const score = floatVal(result.score || (result.confidence ? result.confidence * 100 : 0));
  const level = (result.level || result.severity_tier || '').toLowerCase();
  const category = (result.primary_label || result.category || 'Threat').toUpperCase();

  // Determine badge color tier
  // Red: Critical (Score >= 75 or threats/sextortion/phishing)
  // Orange: High (Score 50-74, harassment, abusive language)
  // Amber: Medium (Score 25-49, suspicious)
  // Safe: Clean (< 25)
  let badgeClass = 'badge-safe';
  let badgeLabel = 'SAFE';

  if (level === 'critical' || score >= 75) {
    badgeClass = 'badge-red';
    badgeLabel = category === 'CLEAN' ? 'CRITICAL' : category;
  } else if (level === 'high' || score >= 50) {
    badgeClass = 'badge-orange';
    badgeLabel = category === 'CLEAN' ? 'HIGH RISK' : category;
  } else if (level === 'medium' || score >= 25) {
    badgeClass = 'badge-amber';
    badgeLabel = category === 'CLEAN' ? 'SUSPICIOUS' : category;
  } else {
    badgeClass = 'badge-safe';
    badgeLabel = 'SAFE';
  }

  // Construct explanatory tooltip explaining why
  let tooltipReason = '';
  if (result.signals && Array.isArray(result.signals) && result.signals.length > 0) {
    const firstSig = result.signals[0];
    tooltipReason = typeof firstSig === 'string' ? firstSig : (firstSig.signal || '');
  } else if (result.explanation) {
    tooltipReason = result.explanation;
  } else if (badgeClass !== 'badge-safe') {
    tooltipReason = `Elevated risk indicators detected for ${category}`;
  } else {
    tooltipReason = 'No malicious or abusive patterns detected.';
  }

  const tooltip = `[${badgeLabel} - Risk Score: ${score.toFixed(0)}/100]\nReason: ${tooltipReason}`;

  const badge = document.createElement('span');
  badge.className = `shieldai-badge ${badgeClass}`;
  badge.textContent = badgeLabel;
  badge.title = tooltip;

  // Append badge next to or inside the message container
  try {
    element.appendChild(badge);
  } catch (e) {
    element.parentElement && element.parentElement.appendChild(badge);
  }

  // Report flagged threat to background for icon badge counter if not safe
  if (badgeClass !== 'badge-safe' && chrome.runtime && chrome.runtime.sendMessage) {
    try {
      chrome.runtime.sendMessage({
        type: 'REPORT_FLAGGED',
        item: {
          category: badgeLabel,
          confidence: score / 100,
          text: (result.text_preview || element.innerText || '').slice(0, 100),
          reason: tooltipReason
        }
      });
    } catch (e) {}
  }
}

function floatVal(val) {
  const f = parseFloat(val);
  return isNaN(f) ? 0.0 : f;
}

// Intersection Observer: prioritize visible messages on screen
const visibleObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      queueElementForScan(entry.target);
    }
  });
}, { root: null, threshold: 0.1 });

// Debounced DOM Scanner
const debouncedScanDOM = debounce(() => {
  if (!isEnabled) return;
  const selector = getMessageSelector();
  if (!selector) return;

  const elements = document.querySelectorAll(selector);
  elements.forEach(el => {
    if (el.getAttribute('data-shieldai-checked') !== 'true') {
      visibleObserver.observe(el);
    }
  });
}, 400);

// MutationObserver: observe incoming chat/email elements
const mutationObserver = new MutationObserver((mutations) => {
  let hasNew = false;
  for (const m of mutations) {
    if (m.addedNodes && m.addedNodes.length > 0) {
      hasNew = true;
      break;
    }
  }
  if (hasNew) debouncedScanDOM();
});

// Kick off initial scan
if (document.body) {
  debouncedScanDOM();
  mutationObserver.observe(document.body, { childList: true, subtree: true });
} else {
  document.addEventListener('DOMContentLoaded', () => {
    debouncedScanDOM();
    mutationObserver.observe(document.body, { childList: true, subtree: true });
  });
}
