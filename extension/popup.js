document.addEventListener('DOMContentLoaded', () => {
  const toggleSwitch = document.getElementById('toggle-switch');
  const statusLabel = document.getElementById('status-label');
  const apiKeyInput = document.getElementById('api-key');
  const privacyBanner = document.getElementById('privacy-banner');
  const flaggedCount = document.getElementById('flagged-count');
  const flaggedList = document.getElementById('flagged-list');

  // Load saved state
  chrome.storage.local.get(['isEnabled', 'apiKey'], (result) => {
    if (result.isEnabled !== undefined) {
      toggleSwitch.checked = result.isEnabled;
      updateUIState(result.isEnabled);
    }
    if (result.apiKey) {
      apiKeyInput.value = result.apiKey;
    }
  });

  // Toggle listener
  toggleSwitch.addEventListener('change', (e) => {
    const isEnabled = e.target.checked;
    chrome.storage.local.set({ isEnabled: isEnabled });
    updateUIState(isEnabled);
  });

  // API Key listener
  apiKeyInput.addEventListener('change', (e) => {
    chrome.storage.local.set({ apiKey: e.target.value });
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
      
      const score = document.createElement('span');
      score.className = 'item-score';
      score.textContent = (item.confidence * 100).toFixed(0) + '%';
      
      header.appendChild(cat);
      header.appendChild(score);
      li.appendChild(header);
      
      const preview = document.createElement('div');
      preview.className = 'item-preview';
      preview.textContent = item.text;
      li.appendChild(preview);
      
      if (item.threatIntel) {
        const ti = document.createElement('div');
        ti.className = 'item-ti';
        ti.textContent = `Threat Intel: ${item.threatIntel}`;
        li.appendChild(ti);
      }
      
      flaggedList.appendChild(li);
    });
  }
});
