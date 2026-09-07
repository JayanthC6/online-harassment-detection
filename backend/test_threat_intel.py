import unittest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ml.adapters.threat_intel import analyze_text_for_threat_intel

class TestThreatIntel(unittest.TestCase):
    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_high_risk_typosquatting(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = "paypal.com"
        mock_sb.return_value = "safe" # Typosquatting overrides Safe Browsing if Safe Browsing is clean
        mock_age.return_value = 100
        
        result = analyze_text_for_threat_intel("Check this out: http://paypa1.com/login")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "High Risk")
        self.assertEqual(urls[0]["risk_score"], 85)
        self.assertIn("Typosquatting", urls[0]["reason"])

    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_high_risk_safe_browsing(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = None
        mock_sb.return_value = "SOCIAL_ENGINEERING"
        mock_age.return_value = 100
        
        result = analyze_text_for_threat_intel("Check this out: http://evil.com/login")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "High Risk")
        self.assertEqual(urls[0]["risk_score"], 90)
        self.assertIn("Google Safe Browsing", urls[0]["reason"])

    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_suspicious_domain(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = None
        mock_sb.return_value = "safe"
        mock_age.return_value = 14 # < 30 days
        
        result = analyze_text_for_threat_intel("Check this out: http://newsite.com/login")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "Suspicious")
        self.assertEqual(urls[0]["risk_score"], 40)
        self.assertIn("Suspiciously New Domain", urls[0]["reason"])

    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_unknown_domain_timeout_whois(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = None
        mock_sb.return_value = "safe"
        mock_age.return_value = None # WHOIS failed
        
        result = analyze_text_for_threat_intel("Check this out: http://unknown.com/login")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "Unknown")
        self.assertEqual(urls[0]["risk_score"], 25)
        self.assertIn("Verification Failed / Timed Out", urls[0]["reason"])

    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_unknown_domain_timeout_sb(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = None
        mock_sb.return_value = None # Safe Browsing failed
        mock_age.return_value = 100
        
        result = analyze_text_for_threat_intel("Check this out: http://unknown.com/login")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "Unknown")
        self.assertEqual(urls[0]["risk_score"], 25)
        self.assertIn("Verification Failed / Timed Out", urls[0]["reason"])

    @patch('ml.adapters.threat_intel.check_safe_browsing')
    @patch('ml.adapters.threat_intel.check_domain_age')
    @patch('ml.adapters.threat_intel.check_typosquatting')
    def test_safe_domain(self, mock_squat, mock_age, mock_sb):
        mock_squat.return_value = None
        mock_sb.return_value = "safe"
        mock_age.return_value = 100
        
        result = analyze_text_for_threat_intel("Check this out: http://google.com")
        urls = result["malicious_urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["status"], "Safe")
        self.assertEqual(urls[0]["risk_score"], 0)
        self.assertIn("Verified Clean", urls[0]["reason"])

if __name__ == '__main__':
    unittest.main()
