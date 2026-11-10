const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const testPageHtmlPath = path.join(rootDir, 'extension', 'test_page.html');
const contentJsPath = path.join(rootDir, 'extension', 'content.js');
const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

if (!fs.existsSync(testPageHtmlPath)) {
  console.error('test_page.html not found at', testPageHtmlPath);
  process.exit(1);
}
if (!fs.existsSync(contentJsPath)) {
  console.error('content.js not found at', contentJsPath);
  process.exit(1);
}

const rawHtml = fs.readFileSync(testPageHtmlPath, 'utf-8');
const contentJs = fs.readFileSync(contentJsPath, 'utf-8');

// Build test harness runner HTML
const runnerHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>ShieldAI Extension Browser Automated Test</title>
</head>
<body>
  ${rawHtml}

  <script>
    // 1. Mock Chrome Extension API environment
    window.chrome = {
      storage: {
        local: {
          get: (keys, cb) => cb({ isEnabled: true, showSafeBadges: false, showUnsupportedBadges: false, disabledSites: [] }),
          set: (obj, cb) => { if (cb) cb(); }
        },
        onChanged: { addListener: () => {} }
      },
      runtime: {
        lastError: null,
        sendMessage: (msg, cb) => {
          if (msg.type === 'CHECK_BATCH') {
            const items = msg.items || [];
            const results = items.map(item => {
              const text = item.text || '';
              if (text.includes('sbi-kyc-update.xyz')) {
                return { id: item.id, result: { score: 88.0, level: 'critical', primary_label: 'Phishing', language_supported: true } };
              } else if (text.includes('worthless piece of trash')) {
                return { id: item.id, result: { score: 70.0, level: 'high', primary_label: 'Harassment', language_supported: true } };
              } else if (text.includes('murder you tonight')) {
                return { id: item.id, result: { score: 92.0, level: 'critical', primary_label: 'Threat', language_supported: true } };
              } else {
                // Safe paragraph
                return { id: item.id, result: { score: 0.0, level: 'low', primary_label: 'Clean', language_supported: true } };
              }
            });
            if (cb) cb({ status: 'success', results: results });
          } else if (msg.type === 'REPORT_FLAGGED') {
            // Handled
          }
        }
      }
    };

    // Override IntersectionObserver for immediate deterministic scanning in headless mode
    window.IntersectionObserver = class {
      constructor(callback) { this.callback = callback; }
      observe(target) {
        this.callback([{ target: target, isIntersecting: true }]);
      }
      unobserve() {}
      disconnect() {}
    };
  </script>

  <!-- Inject ShieldAI Content Script -->
  <script>
    try {
      ${contentJs}
    } catch(e) {
      window.__content_js_error = e.message + ' at ' + e.stack;
    }
  </script>

  <script>
    const debug = [];
    if (window.__content_js_error) {
      debug.push('Content.js ERROR: ' + window.__content_js_error);
    }
    debug.push('Testing scanDOM...');
    const candidates = document.querySelectorAll('p, li, blockquote, div, span');
    debug.push('Candidates count: ' + candidates.length);
    if (window.__shieldai_scanDOM) {
      debug.push('Calling scanDOM...');
      window.__shieldai_scanDOM();
    } else {
      debug.push('__shieldai_scanDOM is missing!');
    }
    if (window.__shieldai_flushBatch) {
      debug.push('Calling flushBatch...');
      window.__shieldai_flushBatch();
    } else {
      debug.push('__shieldai_flushBatch is missing!');
    }

    // Inspect results after batch injection
    setTimeout(() => {
      // Find all elements that received a badge
      const badges = document.querySelectorAll('.shieldai-badge');
      const badgedParentIds = [];
      badges.forEach(b => {
        const parent = b.closest('p, div, li, blockquote') || b.parentElement;
        if (parent && parent.id) {
          badgedParentIds.push(parent.id);
        }
      });

      const report = {
        debug: debug,
        total_badges: badges.length,
        badged_elements: badgedParentIds.sort(),
        safe_p_has_badge: !!document.querySelector('#safe-p .shieldai-badge'),
        phishing_p_has_badge: !!document.querySelector('#phishing-p .shieldai-badge'),
        abusive_p_has_badge: !!document.querySelector('#abusive-p .shieldai-badge'),
        threat_p_has_badge: !!document.querySelector('#threat-p .shieldai-badge'),
        ui_controls_have_badge: document.querySelectorAll('#ui-controls-card .shieldai-badge').length > 0,
        nav_has_badge: document.querySelectorAll('#site-header .shieldai-badge').length > 0,
        footer_has_badge: document.querySelectorAll('#site-footer .shieldai-badge').length > 0
      };

      const outDiv = document.createElement('div');
      outDiv.id = 'shieldai-test-results';
      outDiv.textContent = 'SHIELDAI_TEST_JSON:' + JSON.stringify(report);
      document.body.appendChild(outDiv);
    }, 200);
  </script>
</body>
</html>`;

const tempRunnerPath = path.join(rootDir, 'extension', 'temp_runner.html');
fs.writeFileSync(tempRunnerPath, runnerHtml, 'utf-8');

try {
  // Run headless Chrome
  const stdout = execFileSync(chromePath, [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--dump-dom',
    '--virtual-time-budget=2000',
    `file://${tempRunnerPath.replace(/\\/g, '/')}`
  ], { encoding: 'utf-8' });

  const match = stdout.match(/SHIELDAI_TEST_JSON:(\{.*?\})/);
  if (!match) {
    console.error('Failed to locate test results in DOM output');
    console.error('Chrome stdout preview:', stdout.slice(0, 500));
    process.exit(1);
  }

  const result = JSON.parse(match[1]);
  console.log('Automated Browser Test Report:', JSON.stringify(result, null, 2));

  // Assertions
  const expectedBadged = ['abusive-p', 'phishing-p', 'threat-p'].sort();
  const actualBadged = result.badged_elements.sort();

  if (result.total_badges !== 3) {
    console.error(`Assertion failed: Expected exactly 3 badges, got ${result.total_badges}`);
    process.exit(1);
  }

  if (JSON.stringify(actualBadged) !== JSON.stringify(expectedBadged)) {
    console.error(`Assertion failed: Expected badged elements ${JSON.stringify(expectedBadged)}, got ${JSON.stringify(actualBadged)}`);
    process.exit(1);
  }

  if (result.safe_p_has_badge) {
    console.error('Assertion failed: Safe paragraph falsely received a badge');
    process.exit(1);
  }

  if (result.ui_controls_have_badge || result.nav_has_badge || result.footer_has_badge) {
    console.error('Assertion failed: UI controls, nav, or footer falsely received a badge');
    process.exit(1);
  }

  console.log('[SUCCESS] Automated browser test passed: only the 3 risky paragraphs received badges and nothing else.');
} finally {
  if (fs.existsSync(tempRunnerPath)) {
    fs.unlinkSync(tempRunnerPath);
  }
}
