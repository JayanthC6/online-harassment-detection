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

    def test_url_shortener_detected(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel('Check this: http://bit.ly/1234')
        self.assertIn('threat_signals', result)
        self.assertEqual(len(result['threat_signals']['url_shorteners']), 1)
        self.assertEqual(result['threat_signals']['url_shorteners'][0]['url'], 'http://bit.ly/1234')
        self.assertIn('A URL shortener was detected', result['threat_signals']['url_shorteners'][0]['reason'])

    def test_ip_based_url_detected(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel('Login here: http://192.168.1.100/admin')
        self.assertIn('threat_signals', result)
        self.assertEqual(len(result['threat_signals']['ip_based_urls']), 1)
        self.assertEqual(result['threat_signals']['ip_based_urls'][0]['url'], 'http://192.168.1.100/admin')
        self.assertIn('IP-based URL was detected', result['threat_signals']['ip_based_urls'][0]['reason'])

    def test_social_engineering_credential(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("Please verify your password")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("credential_request", result["threat_signals"]["social_engineering"]["indicators"])

    def test_social_engineering_otp(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("send me the code")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("otp_code_request", result["threat_signals"]["social_engineering"]["indicators"])

    def test_social_engineering_account_verification(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("login to confirm")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("account_verification_pressure", result["threat_signals"]["social_engineering"]["indicators"])

    def test_social_engineering_payment(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("wire me some money")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("payment_request", result["threat_signals"]["social_engineering"]["indicators"])

    def test_social_engineering_gift_card(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("buy an apple card")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("gift_card_request", result["threat_signals"]["social_engineering"]["indicators"])
        
    def test_social_engineering_crypto(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("send bitcoin")
        self.assertTrue(result["threat_signals"]["social_engineering"]["detected"])
        self.assertIn("crypto_payment_request", result["threat_signals"]["social_engineering"]["indicators"])

    def test_urgency_single(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("This is urgent")
        self.assertTrue(result["threat_signals"]["urgency"]["detected"])
        self.assertEqual(result["threat_signals"]["urgency"]["count"], 1)

    def test_urgency_multiple(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("This is urgent! Act now!")
        self.assertTrue(result["threat_signals"]["urgency"]["detected"])
        self.assertEqual(result["threat_signals"]["urgency"]["count"], 2)

    def test_brand_impersonation(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("I am from Microsoft Support")
        self.assertTrue(result["threat_signals"]["brand_impersonation"]["detected"])
        self.assertIn("Microsoft", result["threat_signals"]["brand_impersonation"]["brands"])

    def test_brand_mention_no_impersonation(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("I bought a Microsoft Xbox")
        self.assertFalse(result["threat_signals"]["brand_impersonation"]["detected"])

    def test_dangerous_scheme_javascript(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("Click here: javascript:alert(1)")
        schemes = result["threat_signals"]["dangerous_schemes"]
        self.assertEqual(len(schemes), 1)
        self.assertEqual(schemes[0]["scheme"], "javascript")
        
    def test_dangerous_scheme_data(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("data:text/html,<html>")
        schemes = result["threat_signals"]["dangerous_schemes"]
        self.assertEqual(len(schemes), 1)
        self.assertEqual(schemes[0]["scheme"], "data")

    def test_normal_https_unaffected(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel("https://google.com")
        schemes = result["threat_signals"]["dangerous_schemes"]
        self.assertEqual(len(schemes), 0)
        urls = result["urls"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["url"], "https://google.com")

if __name__ == '__main__':
    unittest.main()
    def test_url_shortener_detected(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel('Check this: http://bit.ly/1234')
        self.assertIn('threat_signals', result)
        self.assertEqual(len(result['threat_signals']['url_shorteners']), 1)
        self.assertEqual(result['threat_signals']['url_shorteners'][0]['url'], 'http://bit.ly/1234')
        self.assertIn('A URL shortener was detected', result['threat_signals']['url_shorteners'][0]['reason'])

    def test_ip_based_url_detected(self):
        from ml.adapters.threat_intel import analyze_text_for_threat_intel
        result = analyze_text_for_threat_intel('Login here: http://192.168.1.100/admin')
        self.assertIn('threat_signals', result)
        self.assertEqual(len(result['threat_signals']['ip_based_urls']), 1)
        self.assertEqual(result['threat_signals']['ip_based_urls'][0]['url'], 'http://192.168.1.100/admin')
        self.assertIn('IP-based URL was detected', result['threat_signals']['ip_based_urls'][0]['reason'])
