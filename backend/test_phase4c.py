import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.prediction_service import PredictionService

class TestPhase4C(unittest.TestCase):
    def test_no_signals(self):
        result = {"risk_score": 0, "category": "clean", "confidence": 0.99, "secondary_labels": {}}
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertEqual(res["threat_signal_summary"]["detected"], False)
        self.assertEqual(len(res["threat_signal_summary"]["categories"]), 0)

    def test_single_se_indicator(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "social_engineering": {
                        "detected": True,
                        "indicators": ["credential_request"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertTrue(res["threat_signal_summary"]["detected"])
        self.assertIn("social_engineering", res["threat_signal_summary"]["categories"])
        self.assertEqual(res["threat_signal_summary"]["count"], 1)
        self.assertIn("A potential credential-request indicator was detected.", res["flagging_reasons"])

    def test_multiple_se_indicators_grouped(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "social_engineering": {
                        "detected": True,
                        "indicators": ["credential_request", "otp_code_request"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("A potential credential-request indicator was detected.", res["flagging_reasons"])
        self.assertIn("A potential otp-code-request indicator was detected.", res["flagging_reasons"])
        self.assertEqual(res["threat_signal_summary"]["count"], 1) # count is number of categories

    def test_single_urgency_indicator(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "urgency": {
                        "detected": True,
                        "count": 1,
                        "indicators": ["urgent"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertTrue(res["threat_signal_summary"]["detected"])
        self.assertIn("urgency", res["threat_signal_summary"]["categories"])
        self.assertIn("An urgency indicator was detected.", res["flagging_reasons"])

    def test_multiple_urgency_indicators(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "urgency": {
                        "detected": True,
                        "count": 2,
                        "indicators": ["urgent", "act now"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("Multiple urgency indicators were detected.", res["flagging_reasons"])

    def test_brand_impersonation(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "brand_impersonation": {
                        "detected": True,
                        "brands": ["Microsoft"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("A potential brand impersonation indicator involving Microsoft was detected.", res["flagging_reasons"])
        self.assertIn("brand_impersonation", res["threat_signal_summary"]["categories"])

    def test_dangerous_scheme(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "dangerous_schemes": [{"scheme": "javascript"}]
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("A potentially dangerous URL scheme was detected.", res["flagging_reasons"])

    def test_url_shortener(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "url_shorteners": [{"reason": "A URL shortener was detected, so the final destination is not visible."}]
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("A URL shortener was detected, so the final destination is not visible.", res["flagging_reasons"])

    def test_ip_based_url(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "ip_based_urls": [{"reason": "An IP-based URL was detected instead of a conventional domain name."}]
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("An IP-based URL was detected instead of a conventional domain name.", res["flagging_reasons"])

    def test_hibp_explanation(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "emails": [{"email": "test@test.com", "breach_count": 3}]
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        self.assertIn("An email address in the submitted content appears in known data-breach records.", res["flagging_reasons"])
        self.assertNotIn("test@test.com", " ".join(res["flagging_reasons"]))

    def test_no_duplicate_flagging_reasons(self):
        result = {
            "risk_score": 0,
            "category": "clean",
            "confidence": 0.99,
            "secondary_labels": {},
            "threat_intel": {
                "threat_signals": {
                    "social_engineering": {
                        "detected": True,
                        "indicators": ["credential_request", "credential_request"]
                    }
                }
            }
        }
        res = PredictionService.attach_risk_and_similarity(result, "hello")
        count = res["flagging_reasons"].count("A potential credential-request indicator was detected.")
        self.assertEqual(count, 1)

    def test_stable_explanation_ordering(self):
        result1 = {
            "risk_score": 80,
            "category": "high",
            "confidence": 0.99,
            "secondary_labels": {"harassment": 0.9},
            "threat_intel": {
                "emails": [{"email": "x@x.com", "breach_count": 1}],
                "threat_signals": {
                    "social_engineering": {"detected": True, "indicators": ["credential_request"]},
                    "urgency": {"detected": True, "count": 2, "indicators": ["urgent", "now"]}
                }
            }
        }
        res1 = PredictionService.attach_risk_and_similarity(result1, "hello")
        
        result2 = {
            "risk_score": 80,
            "category": "high",
            "confidence": 0.99,
            "secondary_labels": {"harassment": 0.9},
            "threat_intel": {
                "emails": [{"email": "x@x.com", "breach_count": 1}],
                "threat_signals": {
                    "social_engineering": {"detected": True, "indicators": ["credential_request"]},
                    "urgency": {"detected": True, "count": 2, "indicators": ["urgent", "now"]}
                }
            }
        }
        res2 = PredictionService.attach_risk_and_similarity(result2, "hello")
        
        self.assertEqual(res1["flagging_reasons"], res2["flagging_reasons"])

if __name__ == '__main__':
    unittest.main()
