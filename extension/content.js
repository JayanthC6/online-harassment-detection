const CONFIDENCE_THRESHOLD = 0.6;
let isEnabled = true;

// Check extension state
if (chrome.runtime && chrome.runtime.sendMessage) {
  try {
    chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response) => {
      if (response && response.isEnabled !== undefined) {
        isEnabled = response.isEnabled;
      }
    });
  } catch (e) {}
}

// Update state when toggled
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.isEnabled) {
    isEnabled = changes.isEnabled.newValue;
  }
});

// Utility to debounce function calls
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Check if a node is a message node we care about
function getMessageSelector() {
  const hostname = window.location.hostname;
  if (hostname.includes('mail.google.com')) {
    // Gmail email body containers
    return '.a3s.aiL, div[role="listitem"] .a3s';
  } else if (hostname.includes('web.whatsapp.com')) {
    // WhatsApp Web message containers
    return 'div.message-in, div.message-out, span.selectable-text';
  }
  return null;
}

function processMessageElement(el) {
  if (!isEnabled) return;
  
  // Deduplication: prevent redundant checks
  if (el.getAttribute('data-shieldai-checked') === 'true') {
    return;
  }
  
  // Mark as checked immediately to prevent concurrent duplicate checks
  el.setAttribute('data-shieldai-checked', 'true');
  
  let text = el.innerText || el.textContent;
  if (!text || text.trim().length < 5) return;
  
  // Truncate text to avoid hitting the backend's 2000 character limit for long emails
  if (text.length > 1950) {
    text = text.substring(0, 1950);
  }
  
  // Safety check: if extension was reloaded, chrome.runtime becomes undefined
  if (!chrome.runtime || !chrome.runtime.sendMessage) return;
  
  try {
    chrome.runtime.sendMessage({ type: 'CHECK_PREDICT', text: text }, (response) => {
      if (!response || response.status !== 'success' || !response.data) return;
      
      const result = response.data;
    
    const isThreat = result.confidence >= CONFIDENCE_THRESHOLD && 
        (result.primary_label === 'Phishing' || result.primary_label === 'Scam' || 
         result.primary_label === 'Toxicity' || result.primary_label === 'Threat' ||
         result.primary_label === 'Cyberbullying / Harassment' || result.primary_label === 'Profanity');
         
    // Inject badge for ALL scanned messages
    injectBadge(el, result, isThreat);
    
    // Only report to background script (increment popup count) if it's an actual threat
    if (isThreat) {
      chrome.runtime.sendMessage({
        type: 'REPORT_FLAGGED',
        item: {
          category: result.primary_label,
          confidence: result.confidence,
          text: result.text_preview,
          threatIntel: result.threat_intel ? Object.keys(result.threat_intel.urls || {}).join(', ') : null
        }
      });
    }
    }); // <-- Added missing callback closure
  } catch (e) {
    // Ignore context invalidated errors silently
  }
}

function injectBadge(element, result, isThreat) {
  // Prevent duplicate badges on the exact same element if somehow called twice
  if (element.querySelector('.shieldai-badge')) return;
  
  const badge = document.createElement('span');
  badge.className = isThreat ? 'shieldai-badge badge-threat' : 'shieldai-badge badge-safe';
  
  if (isThreat) {
    badge.textContent = result.primary_label;
  } else {
    badge.textContent = 'SAFE';
  }
  
  let tooltip = `Score: ${(result.confidence * 100).toFixed(0)}%`;
  if (result.threat_intel && result.threat_intel.urls && Object.keys(result.threat_intel.urls).length > 0) {
    tooltip += `\nThreat Intel: Detected known malicious URLs`;
  } else if (!isThreat) {
    tooltip += '\nNo threats detected';
  }
  badge.title = tooltip;
  
  // Append inside the message bubble for layout stability
  element.appendChild(badge);
}

// Set up Intersection Observer to only scan visible messages
const observerOptions = {
  root: null,
  rootMargin: '0px',
  threshold: 0.1
};

const messageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      processMessageElement(entry.target);
    }
  });
}, observerOptions);

// Observe DOM mutations to find newly added messages (e.g. infinite scroll)
const debouncedScanDOM = debounce(() => {
  if (!isEnabled) return;
  
  const selector = getMessageSelector();
  if (!selector) return;
  
  const elements = document.querySelectorAll(selector);
  elements.forEach(el => {
    if (el.getAttribute('data-shieldai-checked') !== 'true') {
      messageObserver.observe(el);
    }
  });
}, 1000);

const mutationObserver = new MutationObserver((mutations) => {
  let shouldScan = false;
  for (let m of mutations) {
    if (m.addedNodes.length > 0) {
      shouldScan = true;
      break;
    }
  }
  if (shouldScan) debouncedScanDOM();
});

// Start observing
debouncedScanDOM();
mutationObserver.observe(document.body, { childList: true, subtree: true });
