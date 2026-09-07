import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ml.adapters.threat_intel import mask_pii, extract_pii

class TestPIIMasking(unittest.TestCase):
    
    def test_aadhaar_true_positive(self):
        cases = [
            ("My Aadhaar is 2345 6789 1234.", "[AADHAAR REDACTED]"),
            ("ID: 9876 5432 1098", "[AADHAAR REDACTED]"),
            ("Aadhaar: 345612345678", "[AADHAAR REDACTED]"),
        ]
        for text, expected in cases:
            self.assertIn(expected, mask_pii(text))
            self.assertIn("Aadhaar", extract_pii(text))
            
    def test_aadhaar_false_positive(self):
        cases = [
            "Starts with zero: 0123 4567 8901",
            "Starts with one: 1234 5678 9012",
            "Price is 2345 dollars and 6789 cents",
        ]
        for text in cases:
            self.assertNotIn("[AADHAAR REDACTED]", mask_pii(text))
            self.assertNotIn("Aadhaar", extract_pii(text))
            
    def test_pan_true_positive(self):
        text = "My PAN is ABCDE1234F"
        self.assertIn("[PAN REDACTED]", mask_pii(text))
        self.assertIn("PAN", extract_pii(text))
        
    def test_phone_true_positive(self):
        cases = [
            ("Call me at +91-9876543210", "[PHONE REDACTED]"),
            ("My number is 9876543210", "[PHONE REDACTED]"),
            ("WhatsApp +91 8765432109", "[PHONE REDACTED]"),
            ("Reach out 7890123456", "[PHONE REDACTED]")
        ]
        for text, expected in cases:
            self.assertIn(expected, mask_pii(text))
            self.assertIn("Phone", extract_pii(text))
            
    def test_phone_false_positive(self):
        cases = [
            "Price is 1234567890", # Starts with 1
            "Random ID 5678901234", # Starts with 5
            "Date: 2026-09-07",
        ]
        for text in cases:
            self.assertNotIn("[PHONE REDACTED]", mask_pii(text))
            self.assertNotIn("Phone", extract_pii(text))
            
    def test_aadhaar_phone_overlap(self):
        # A 12-digit Aadhaar whose last 10 digits form a valid phone number (starts with 9)
        # e.g., 239876543210
        # If order is wrong, it might redact the 9876543210 as Phone, leaving "23[PHONE REDACTED]"
        text = "Here is my ID: 239876543210."
        masked = mask_pii(text)
        self.assertEqual(masked, "Here is my ID: [AADHAAR REDACTED].")
        self.assertNotIn("[PHONE REDACTED]", masked)
        
        extracted = extract_pii(text)
        self.assertIn("Aadhaar", extracted)
        self.assertNotIn("Phone", extracted)

if __name__ == '__main__':
    unittest.main()
