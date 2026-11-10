import os
import subprocess
import pytest

def test_extension_test_page_automated_browser():
    """
    Automated browser test verifying that only the 3 risky paragraphs get badges
    (phishing, abusive, threat) and nothing else on extension/test_page.html
    (no badges on safe paragraph, nav, header, footer, buttons, or short ALL-CAPS UI labels).
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    script_path = os.path.join(repo_root, "scripts", "verify_extension_browser.js")
    assert os.path.exists(script_path), f"Verification script missing at {script_path}"

    res = subprocess.run(["node", script_path], capture_output=True, text=True)
    assert res.returncode == 0, f"Automated browser test failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "only the 3 risky paragraphs received badges and nothing else" in res.stdout

