// ShieldAI Content Script — Message Scanner & Threat Badging (Manifest V3)
(() => {
  let isEnabled = true;
  let showSafeBadges = false;
  let showUnsupportedBadges = false;
  let isSiteDisabled = false;
  const currentHostname = window.location.hostname;

  const pendingBatch = [];
  let batchTimeout = null;
  let lastBatchDispatchTime = 0;
  const MIN_BATCH_INTERVAL_MS = 350; // Throttle rate limit
  const MAX_BATCH_SIZE = 30; // Batch cap

  // Load configuration from chrome.storage.local
  function loadConfig() {
    if (typeof chrome === 'undefined' || !chrome.storage || !chrome.storage.local) return;
    chrome.storage.local.get(['isEnabled', 'showSafeBadges', 'showUnsupportedBadges', 'disabledSites'], (cfg) => {
      if (cfg.isEnabled !== undefined) isEnabled = cfg.isEnabled;
      if (cfg.showSafeBadges !== undefined) showSafeBadges = Boolean(cfg.showSafeBadges);
      if (cfg.showUnsupportedBadges !== undefined) showUnsupportedBadges = Boolean(cfg.showUnsupportedBadges);
      if (Array.isArray(cfg.disabledSites)) {
        isSiteDisabled = cfg.disabledSites.includes(currentHostname);
      } else {
        isSiteDisabled = false;
      }

      if (!isEnabled || isSiteDisabled) {
        hideAllBadges();
      } else {
        showAllBadges();
        debouncedScanDOM();
      }
    });
  }

  loadConfig();

  // Listen for configuration updates from popup
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.onChanged) {
    chrome.storage.onChanged.addListener((changes, namespace) => {
      if (namespace === 'local') {
        if (changes.isEnabled !== undefined) {
          isEnabled = changes.isEnabled.newValue;
        }
        if (changes.showSafeBadges !== undefined) {
          showSafeBadges = Boolean(changes.showSafeBadges.newValue);
        }
        if (changes.showUnsupportedBadges !== undefined) {
          showUnsupportedBadges = Boolean(changes.showUnsupportedBadges.newValue);
        }
        if (changes.disabledSites !== undefined) {
          const list = changes.disabledSites.newValue || [];
          isSiteDisabled = list.includes(currentHostname);
        }

        if (!isEnabled || isSiteDisabled) {
          hideAllBadges();
        } else {
          showAllBadges();
          debouncedScanDOM();
        }
      }
    });
  }

  function hideAllBadges() {
    document.querySelectorAll('.shieldai-badge').forEach(b => {
      b.style.display = 'none';
    });
  }

  function showAllBadges() {
    document.querySelectorAll('.shieldai-badge').forEach(b => {
      if (b.classList.contains('badge-safe') && !showSafeBadges) {
        b.style.display = 'none';
      } else if (b.classList.contains('badge-purple') && !showUnsupportedBadges) {
        b.style.display = 'none';
      } else {
        b.style.display = 'inline-flex';
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

  // Site-specific high-priority selectors
  function getSiteSpecificSelector() {
    if (currentHostname.includes('mail.google.com')) {
      return '.a3s.aiL, div[role="listitem"] .a3s';
    } else if (currentHostname.includes('web.whatsapp.com')) {
      return 'div.message-in, div.message-out, span.selectable-text';
    }
    // Specific test harness selectors
    return '.chat-message, .message-content, .msg-text, [data-message], .message-bubble, .message-body';
  }

  // Generic fallback validator: p, li, blockquote, div/span of 15-600 chars with no block children
  const BLOCK_CHILDREN_SELECTOR = 'p, div, ul, ol, li, blockquote, pre, table, section, article, header, footer, h1, h2, h3, h4, h5, h6, form';
  const EXCLUDED_TAGS = new Set(['SCRIPT', 'STYLE', 'CODE', 'PRE', 'KBD', 'SAMP', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'BUTTON', 'NOSCRIPT']);

  function isEligibleGenericNode(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return false;
    if (EXCLUDED_TAGS.has(el.tagName)) return false;
    if (el.isContentEditable || el.closest('[contenteditable="true"]')) return false;
    if (el.closest('pre, code, kbd, samp, .shieldai-badge')) return false;

    const tag = el.tagName.toLowerCase();
    if (!['p', 'li', 'blockquote', 'div', 'span'].includes(tag)) return false;

    // Must have no block children
    if (el.querySelector(BLOCK_CHILDREN_SELECTOR)) return false;

    const text = (el.innerText || el.textContent || '').trim();
    return text.length >= 15 && text.length <= 600;
  }

  // Queue an element for batch scanning
  function queueElementForScan(el) {
    if (!isEnabled || isSiteDisabled) return;
    if (!el || el.getAttribute('data-shieldai-checked') === 'true') return;

    // Immediately mark to prevent redundant scans across SPA transitions and scroll events
    el.setAttribute('data-shieldai-checked', 'true');

    const text = (el.innerText || el.textContent || '').trim();
    if (!text || text.length < 5 || text.length > 2000) {
      return;
    }

    pendingBatch.push({ element: el, text: text });

    if (pendingBatch.length >= MAX_BATCH_SIZE) {
      scheduleBatchFlush(0);
    } else if (!batchTimeout) {
      scheduleBatchFlush(MIN_BATCH_INTERVAL_MS);
    }
  }

  function scheduleBatchFlush(delayMs) {
    if (batchTimeout) clearTimeout(batchTimeout);
    batchTimeout = setTimeout(flushBatch, delayMs);
  }

  // Dispatch queued batch to the background service worker
  function flushBatch() {
    batchTimeout = null;
    if (pendingBatch.length === 0 || !isEnabled || isSiteDisabled) return;

    // Rate limiting throttle check
    const now = Date.now();
    const elapsed = now - lastBatchDispatchTime;
    if (elapsed < MIN_BATCH_INTERVAL_MS) {
      scheduleBatchFlush(MIN_BATCH_INTERVAL_MS - elapsed);
      return;
    }

    lastBatchDispatchTime = now;
    const currentBatch = pendingBatch.splice(0, MAX_BATCH_SIZE);
    const texts = currentBatch.map(item => item.text);

    if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendMessage) {
      return;
    }

    try {
      // Content script sends batch to background worker (NEVER calls localhost directly)
      chrome.runtime.sendMessage({ type: 'CHECK_BATCH', texts: texts }, (response) => {
        if (chrome.runtime.lastError) {
          // Extension or backend offline: silently handle without breaking host page
          return;
        }

        if (!response || response.status !== 'success' || !Array.isArray(response.results)) {
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
      // Handled silently
    }
  }

  // Inject colour-coded threat badge
  function injectBadge(element, result) {
    if (!element || element.querySelector('.shieldai-badge')) return;

    const score = parseFloat(result.score || (result.confidence ? result.confidence * 100 : 0)) || 0.0;
    const level = (result.level || result.severity_tier || '').toLowerCase();
    const category = (result.primary_label || result.category || 'Threat').toUpperCase();

    const isUnsupported = result.language_supported === false;
    let badgeClass = 'badge-safe';
    let badgeLabel = 'SAFE';

    if (isUnsupported) {
      if (score >= 50.0) {
        if (level === 'critical' || score >= 75) {
          badgeClass = 'badge-red';
          badgeLabel = category === 'CLEAN' ? 'CRITICAL' : category;
        } else {
          badgeClass = 'badge-orange';
          badgeLabel = category === 'CLEAN' ? 'HIGH RISK' : category;
        }
      } else {
        badgeClass = 'badge-purple';
        badgeLabel = 'UNVERIFIED';
      }
    } else if (level === 'critical' || score >= 75) {
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

    // Requirement: Do not show a badge for clean messages unless "show safe badges" popup option is on
    if (badgeClass === 'badge-safe' && !showSafeBadges) {
      return;
    }

    // Requirement: Do not show a purple badge on every non-English paragraph unless "show unsupported badges" is on
    if (badgeClass === 'badge-purple' && !showUnsupportedBadges) {
      return;
    }

    // Construct explanatory tooltip
    let tooltipReason = '';
    if (isUnsupported) {
      tooltipReason = result.language_note || `Unsupported language/script (${result.language_detected || 'Non-English'}). Results may be unreliable; cannot be verified as safe.`;
    } else if (result.signals && Array.isArray(result.signals) && result.signals.length > 0) {
      const firstSig = result.signals[0];
      tooltipReason = typeof firstSig === 'string' ? firstSig : (firstSig.signal || '');
    } else if (result.explanation) {
      tooltipReason = result.explanation;
    } else if (badgeClass !== 'badge-safe') {
      tooltipReason = `Elevated risk indicators detected for ${category}`;
    } else {
      tooltipReason = 'No malicious or abusive patterns detected.';
    }

    const tooltip = isUnsupported
      ? `[UNVERIFIED - Unsupported Language (${result.language_detected || 'Unknown'})]\nReason: ${tooltipReason}`
      : `[${badgeLabel} - Risk Score: ${score.toFixed(0)}/100]\nReason: ${tooltipReason}`;

    const badge = document.createElement('span');
    badge.className = `shieldai-badge ${badgeClass}`;
    badge.textContent = badgeLabel;
    badge.title = tooltip;

    try {
      element.appendChild(badge);
    } catch (e) {
      element.parentElement && element.parentElement.appendChild(badge);
    }

    // Report flagged threat to background worker
    if (badgeClass !== 'badge-safe' && typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
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

  // IntersectionObserver: prioritizes elements visible in viewport
  const visibleObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        queueElementForScan(entry.target);
      }
    });
  }, { root: null, threshold: 0.1 });

  // DOM Scanner: runs site-specific first, then generic fallback
  function scanDOM() {
    if (!isEnabled || isSiteDisabled) return;

    // 1. Site-specific high-priority scan
    const siteSelector = getSiteSpecificSelector();
    if (siteSelector) {
      const siteElements = document.querySelectorAll(siteSelector);
      siteElements.forEach(el => {
        if (el.getAttribute('data-shieldai-checked') !== 'true') {
          visibleObserver.observe(el);
        }
      });
    }

    // 2. Generic fallback scanner for any page (p, li, blockquote, div, span)
    const candidates = document.querySelectorAll('p, li, blockquote, div, span');
    candidates.forEach(el => {
      if (el.getAttribute('data-shieldai-checked') !== 'true' && isEligibleGenericNode(el)) {
        visibleObserver.observe(el);
      }
    });
  }

  const debouncedScanDOM = debounce(scanDOM, 350);

  // MutationObserver for dynamic infinite scroll and chat arrivals
  const mutationObserver = new MutationObserver((mutations) => {
    let hasAdded = false;
    for (const m of mutations) {
      if (m.addedNodes && m.addedNodes.length > 0) {
        for (const node of m.addedNodes) {
          if (node.nodeType === Node.ELEMENT_NODE && !node.classList?.contains('shieldai-badge')) {
            hasAdded = true;
            break;
          }
        }
      }
      if (hasAdded) break;
    }
    if (hasAdded) debouncedScanDOM();
  });

  // SPA Navigation hooks (popstate, pushState, replaceState)
  window.addEventListener('popstate', () => {
    debouncedScanDOM();
  });

  const originalPushState = history.pushState;
  history.pushState = function(...args) {
    const ret = originalPushState.apply(this, args);
    window.dispatchEvent(new Event('shieldai_navigation'));
    return ret;
  };

  const originalReplaceState = history.replaceState;
  history.replaceState = function(...args) {
    const ret = originalReplaceState.apply(this, args);
    window.dispatchEvent(new Event('shieldai_navigation'));
    return ret;
  };

  window.addEventListener('shieldai_navigation', () => {
    debouncedScanDOM();
  });

  // Initial trigger
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      debouncedScanDOM();
      if (document.body) mutationObserver.observe(document.body, { childList: true, subtree: true });
    });
  } else {
    debouncedScanDOM();
    if (document.body) mutationObserver.observe(document.body, { childList: true, subtree: true });
  }
})();
