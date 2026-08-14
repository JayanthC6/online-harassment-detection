// State management
let isEnabled = true;
const tabFlagCounts = new Map(); // tabId -> { count: number, items: Array }

// Initialize storage
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['isEnabled', 'apiKey'], (result) => {
    if (result.isEnabled !== undefined) {
      isEnabled = result.isEnabled;
    } else {
      chrome.storage.local.set({ isEnabled: true });
    }
  });
});

chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.isEnabled) {
    isEnabled = changes.isEnabled.newValue;
  }
});

// Clean up counts on tab closed
chrome.tabs.onRemoved.addListener((tabId) => {
  tabFlagCounts.delete(tabId);
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'CHECK_PREDICT') {
    if (!isEnabled) {
      sendResponse({ status: 'disabled' });
      return true;
    }
    
    // Fetch API key
    chrome.storage.local.get(['apiKey'], async (result) => {
      const apiKey = result.apiKey || '';
      try {
        const response = await fetch('http://127.0.0.1:5000/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Extension-Api-Key': apiKey,
          },
          body: JSON.stringify({ text: request.text })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        sendResponse({ status: 'success', data: data });
      } catch (error) {
        console.error('Prediction fetch error:', error);
        sendResponse({ status: 'error', error: error.message });
      }
    });
    
    return true; // Keep message channel open for async sendResponse
  }
  
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
      chrome.action.setBadgeBackgroundColor({ color: '#EF4444', tabId: tabId }); // Redaction Red
    }
    sendResponse({ status: 'logged' });
    return false; // synchronous
  }
  
  if (request.type === 'GET_TAB_DATA') {
    // When popup requests data for current tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        const tabId = tabs[0].id;
        const data = tabFlagCounts.get(tabId) || { count: 0, items: [] };
        sendResponse(data);
      } else {
        sendResponse({ count: 0, items: [] });
      }
    });
    return true; // Keep message channel open for async sendResponse
  }
  
  if (request.type === 'GET_STATE') {
    sendResponse({ isEnabled: isEnabled });
    return false;
  }
});
