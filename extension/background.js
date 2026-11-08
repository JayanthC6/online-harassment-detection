// ShieldAI Background Service Worker (Manifest V3)
const DEFAULT_SERVER_URL = 'http://127.0.0.1:5000';
let isEnabled = true;
let serverUrl = DEFAULT_SERVER_URL;
let apiKey = '';
const tabFlagCounts = new Map(); // tabId -> { count: number, items: Array }

// Initialize configuration
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['isEnabled', 'serverUrl', 'apiKey'], (result) => {
    if (result.isEnabled !== undefined) {
      isEnabled = result.isEnabled;
    } else {
      chrome.storage.local.set({ isEnabled: true });
    }
    if (result.serverUrl) {
      serverUrl = result.serverUrl;
    } else {
      chrome.storage.local.set({ serverUrl: DEFAULT_SERVER_URL });
    }
    if (result.apiKey) {
      apiKey = result.apiKey;
    }
  });
});

// Sync configuration changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    if (changes.isEnabled !== undefined) isEnabled = changes.isEnabled.newValue;
    if (changes.serverUrl !== undefined) serverUrl = changes.serverUrl.newValue || DEFAULT_SERVER_URL;
    if (changes.apiKey !== undefined) apiKey = changes.apiKey.newValue || '';
  }
});

// Clean up counts on tab closed
chrome.tabs.onRemoved.addListener((tabId) => {
  tabFlagCounts.delete(tabId);
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 1. Batch Prediction Request from Content Script
  if (request.type === 'CHECK_BATCH') {
    if (!isEnabled) {
      sendResponse({ status: 'disabled', results: [] });
      return true;
    }

    const texts = request.texts || [];
    if (!Array.isArray(texts) || texts.length === 0) {
      sendResponse({ status: 'empty', results: [] });
      return true;
    }

    chrome.storage.local.get(['serverUrl', 'apiKey'], async (cfg) => {
      const baseUrl = (cfg.serverUrl || serverUrl || DEFAULT_SERVER_URL).replace(/\/+$/, '');
      const key = cfg.apiKey || apiKey || '';

      try {
        const response = await fetch(`${baseUrl}/api/batch`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(key ? { 'X-Extension-Api-Key': key } : {})
          },
          body: JSON.stringify({ texts: texts })
        });

        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        const results = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : []);
        sendResponse({ status: 'success', results: results });
      } catch (error) {
        // Backend offline or unreachable: handle gracefully without throwing
        console.warn('[ShieldAI] Batch scan connection warning:', error.message);
        sendResponse({ status: 'offline', error: error.message, results: [] });
      }
    });

    return true; // Keep message channel open for async fetch response
  }

  // 2. Single Message Prediction Fallback
  if (request.type === 'CHECK_PREDICT') {
    if (!isEnabled) {
      sendResponse({ status: 'disabled' });
      return true;
    }

    chrome.storage.local.get(['serverUrl', 'apiKey'], async (cfg) => {
      const baseUrl = (cfg.serverUrl || serverUrl || DEFAULT_SERVER_URL).replace(/\/+$/, '');
      const key = cfg.apiKey || apiKey || '';

      try {
        const response = await fetch(`${baseUrl}/predict`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(key ? { 'X-Extension-Api-Key': key } : {})
          },
          body: JSON.stringify({ text: request.text })
        });

        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        sendResponse({ status: 'success', data: data });
      } catch (error) {
        console.warn('[ShieldAI] Single scan connection warning:', error.message);
        sendResponse({ status: 'offline', error: error.message });
      }
    });

    return true;
  }

  // 3. Report Flagged Threat Item
  if (request.type === 'REPORT_FLAGGED') {
    const tabId = sender.tab ? sender.tab.id : null;
    if (tabId) {
      if (!tabFlagCounts.has(tabId)) {
        tabFlagCounts.set(tabId, { count: 0, items: [] });
      }
      const data = tabFlagCounts.get(tabId);
      data.count += 1;
      data.items.push(request.item);

      // Update badge text on extension icon
      chrome.action.setBadgeText({ text: data.count.toString(), tabId: tabId });
      chrome.action.setBadgeBackgroundColor({ color: '#EF4444', tabId: tabId });
    }
    sendResponse({ status: 'logged' });
    return false;
  }

  // 4. Retrieve Tab Flagged Data for Popup
  if (request.type === 'GET_TAB_DATA') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        const tabId = tabs[0].id;
        const data = tabFlagCounts.get(tabId) || { count: 0, items: [] };
        sendResponse(data);
      } else {
        sendResponse({ count: 0, items: [] });
      }
    });
    return true;
  }

  // 5. Get Current Extension State
  if (request.type === 'GET_STATE') {
    sendResponse({ isEnabled: isEnabled, serverUrl: serverUrl });
    return false;
  }
});
