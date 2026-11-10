document.addEventListener('DOMContentLoaded', () => {
  const toggleSwitch = document.getElementById('toggle-switch');
  const statusLabel = document.getElementById('status-label');
  const serverUrlInput = document.getElementById('server-url');
  const saveUrlBtn = document.getElementById('save-url-btn');
  const urlStatus = document.getElementById('url-status');
  const apiKeyInput = document.getElementById('api-key');
  const privacyBanner = document.getElementById('privacy-banner');
  const flaggedCount = document.getElementById('flagged-count');
  const flaggedList = document.getElementById('flagged-list');
  const showSafeSwitch = document.getElementById('show-safe-switch');
  const showUnsupportedSwitch = document.getElementById('show-unsupported-switch');
  const siteToggleSwitch = document.getElementById('site-toggle-switch');
  const currentDomainLabel = document.getElementById('current-domain-label');

  let currentDomain = '';

  // Get active tab domain for per-site opt-out
  if (chrome.tabs && chrome.tabs.query) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs[0] && tabs[0].url) {
        try {
          const u = new URL(tabs[0].url);
          currentDomain = u.hostname;
          if (currentDomainLabel) {
            currentDomainLabel.textContent = currentDomain || 'local page';
          }
          // Check if disabled on this site
          chrome.storage.local.get(['disabledSites'], (data) => {
            const list = data.disabledSites || [];
            siteToggleSwitch.checked = !list.includes(currentDomain);
          });
        } catch (e) {
          if (currentDomainLabel) currentDomainLabel.textContent = 'file / local page';
        }
      }
    });
  }

  // Load saved settings
  chrome.storage.local.get(['isEnabled', 'serverUrl', 'apiKey', 'showSafeBadges', 'showUnsupportedBadges'], (result) => {
    if (result.isEnabled !== undefined) {
      toggleSwitch.checked = result.isEnabled;
      updateUIState(result.isEnabled);
    }
    if (result.serverUrl) {
      serverUrlInput.value = result.serverUrl;
    } else {
      serverUrlInput.value = 'http://127.0.0.1:5000';
    }
    if (result.apiKey) {
      apiKeyInput.value = result.apiKey;
    }
    if (result.showSafeBadges !== undefined) {
      showSafeSwitch.checked = Boolean(result.showSafeBadges);
    } else {
      showSafeSwitch.checked = false; // default off
    }
    if (result.showUnsupportedBadges !== undefined) {
      showUnsupportedSwitch.checked = Boolean(result.showUnsupportedBadges);
    } else {
      showUnsupportedSwitch.checked = false; // default off
    }
  });

  // Global Toggle listener
  toggleSwitch.addEventListener('change', (e) => {
    const isEnabled = e.target.checked;
    chrome.storage.local.set({ isEnabled: isEnabled });
    updateUIState(isEnabled);
  });

  // Safe badges toggle listener (default off)
  showSafeSwitch.addEventListener('change', (e) => {
    chrome.storage.local.set({ showSafeBadges: e.target.checked });
  });

  // Unsupported language badges toggle listener (default off)
  showUnsupportedSwitch.addEventListener('change', (e) => {
    chrome.storage.local.set({ showUnsupportedBadges: e.target.checked });
  });

  // Per-site toggle listener
  siteToggleSwitch.addEventListener('change', (e) => {
    if (!currentDomain) return;
    const isSiteEnabled = e.target.checked;
    chrome.storage.local.get(['disabledSites'], (data) => {
      let list = data.disabledSites || [];
      if (isSiteEnabled) {
        list = list.filter(d => d !== currentDomain);
      } else {
        if (!list.includes(currentDomain)) {
          list.push(currentDomain);
        }
      }
      chrome.storage.local.set({ disabledSites: list });
    });
  });

  // Save Server URL with optional_host_permissions request
  saveUrlBtn.addEventListener('click', () => {
    let rawUrl = (serverUrlInput.value || '').trim();
    if (!rawUrl) rawUrl = 'http://127.0.0.1:5000';
    
    // Normalize URL
    let urlObj;
    try {
      urlObj = new URL(rawUrl);
    } catch (err) {
      urlStatus.style.color = 'var(--accent-red)';
      urlStatus.textContent = 'Invalid URL format (must start with http:// or https://)';
      return;
    }

    const cleanBaseUrl = urlObj.origin;
    const originPattern = cleanBaseUrl + '/*';

    // If already covered by default host_permissions (127.0.0.1 or localhost on port 5000)
    const isDefault = cleanBaseUrl.includes('127.0.0.1:5000') || cleanBaseUrl.includes('localhost:5000');

    if (isDefault) {
      chrome.storage.local.set({ serverUrl: cleanBaseUrl });
      urlStatus.style.color = 'var(--accent-green)';
      urlStatus.textContent = 'Server URL saved successfully!';
      setTimeout(() => { urlStatus.textContent = ''; }, 3000);
      return;
    }

    // For custom URLs, request host permission
    if (chrome.permissions && chrome.permissions.request) {
      chrome.permissions.request({ origins: [originPattern] }, (granted) => {
        if (granted) {
          chrome.storage.local.set({ serverUrl: cleanBaseUrl });
          urlStatus.style.color = 'var(--accent-green)';
          urlStatus.textContent = 'Host permission granted & URL saved!';
        } else {
          urlStatus.style.color = 'var(--accent-red)';
          urlStatus.textContent = 'Permission denied for custom origin.';
        }
        setTimeout(() => { urlStatus.textContent = ''; }, 4000);
      });
    } else {
      chrome.storage.local.set({ serverUrl: cleanBaseUrl });
      urlStatus.style.color = 'var(--accent-green)';
      urlStatus.textContent = 'URL saved!';
      setTimeout(() => { urlStatus.textContent = ''; }, 3000);
    }
  });

  // API Key listener
  apiKeyInput.addEventListener('change', (e) => {
    chrome.storage.local.set({ apiKey: e.target.value.trim() });
  });

  function updateUIState(isEnabled) {
    if (isEnabled) {
      statusLabel.textContent = 'SCANNING';
      statusLabel.className = 'status-text status-active';
      privacyBanner.classList.remove('hidden');
    } else {
      statusLabel.textContent = 'DISABLED';
      statusLabel.className = 'status-text status-inactive';
      privacyBanner.classList.add('hidden');
    }
  }

  // Fetch flagged items for the current tab
  chrome.runtime.sendMessage({ type: 'GET_TAB_DATA' }, (response) => {
    if (response) {
      flaggedCount.textContent = response.count || 0;
      renderFlaggedItems(response.items || []);
    }
  });

  function renderFlaggedItems(items) {
    flaggedList.innerHTML = '';
    if (items.length === 0) {
      const li = document.createElement('li');
      li.className = 'flagged-item';
      li.style.color = 'var(--text-muted)';
      li.style.textAlign = 'center';
      li.textContent = 'No threats detected on this page.';
      flaggedList.appendChild(li);
      return;
    }

    items.forEach(item => {
      const li = document.createElement('li');
      li.className = 'flagged-item';
      
      const header = document.createElement('div');
      header.className = 'item-header';
      
      const cat = document.createElement('span');
      cat.className = 'item-category';
      cat.textContent = item.category;
      
      const isUnsupp = item.category === 'UNVERIFIED' || item.level === 'unsupported';
      const score = document.createElement('span');
      score.className = 'item-score';
      score.textContent = isUnsupp ? 'UNVERIFIED' : (item.confidence * 100).toFixed(0) + '%';
      
      header.appendChild(cat);
      header.appendChild(score);
      li.appendChild(header);
      
      const preview = document.createElement('div');
      preview.className = 'item-preview';
      preview.textContent = item.text;
      li.appendChild(preview);
      
      if (item.threatIntel || item.reason) {
        const ti = document.createElement('div');
        ti.className = 'item-ti';
        ti.textContent = item.reason || `Threat Intel: ${item.threatIntel}`;
        li.appendChild(ti);
      }
      
      flaggedList.appendChild(li);
    });
  }
});
