import sys
import os
import random
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from services.model_service import ModelService

def main():
    tsv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data", "sms_tune.tsv")
    df = pd.read_csv(tsv_path, sep="\t", names=["label", "text"])
    
    ms = ModelService.get_instance()
    
    false_negatives = []
    false_positives = []
    
    for idx, row in df.iterrows():
        text = str(row["text"])
        is_spam_true = 1 if row["label"] == "spam" else 0
        
        r_res = ms.evaluate_rules(text)
        r_cats = r_res["category_scores"]
        max_fraud = max(r_cats.get("scam", 0.0), r_cats.get("phishing", 0.0), r_cats.get("sextortion", 0.0))
        is_fraud_flagged = 1 if max_fraud >= 50.0 else 0
        
        if is_spam_true == 1 and is_fraud_flagged == 0:
            false_negatives.append((idx, text))
        elif is_spam_true == 0 and is_fraud_flagged == 1:
            false_positives.append((idx, text, [s["signal"] for s in r_res["signals"]]))

    print(f"Total rows in Tune: {len(df)}")
    print(f"Total True Spam: {len(df[df['label'] == 'spam'])}")
    print(f"Total False Negatives on Tune: {len(false_negatives)}")
    print(f"Total False Positives on Tune: {len(false_positives)}")
    
    # Randomly sample 100 false negatives with seed 42
    random.seed(42)
    sample_100 = random.sample(false_negatives, min(100, len(false_negatives)))
    
    print("\n" + "="*80)
    print("CATEGORIZATION OF 100 RANDOMLY SAMPLED FALSE NEGATIVES (SEED 42)")
    print("="*80)
    
    import re
    # Patterns for categorization:
    # 1. prize/lottery scam: won, prize, claim, cash, lottery, award, sweepstakes, selected, gift
    # 2. phishing/credential: verify, password, account, security, bank, login, kyc
    # 3. premium-rate subscription marketing: txt, text to, call \d+, cost, per week, /week, \.pw, \.wk, min, ringtone, chat, tone, service, subscribe, dating, flirty, sub, 150p, 50p, £\d, mobile, offer, free
    
    cats = {
        "prize/lottery scam": [],
        "phishing/credential": [],
        "premium-rate subscription marketing": [],
        "other": []
    }
    
    for idx, text in sample_100:
        tl = text.lower()
        if any(w in tl for w in ["won", "prize", "lottery", "cash", "award", "sweepstakes", "claim", "selected", "guaranteed cash", "draw"]):
            cats["prize/lottery scam"].append((idx, text))
        elif any(w in tl for w in ["account", "password", "bank", "login", "credential", "verify", "security update", "kyc"]):
            cats["phishing/credential"].append((idx, text))
        elif any(w in tl for w in ["ringtone", "poly", "chat", "babe", "dating", "flirt", "sex", "tone", "sub", "subscription", "wk", "/min", "cost", "p/min", "pence", "txt", "text to", "reply", "call 09", "call 08", "rate", "operator", "handset", "free mobile", "camera phone", "upgrade"]):
            cats["premium-rate subscription marketing"].append((idx, text))
        else:
            cats["other"].append((idx, text))
            
    print(f"\nCategorization Summary (Sample of {len(sample_100)}):")
    for cat_name, items in cats.items():
        print(f"  - {cat_name}: {len(items)} ({len(items)}%)")
        
    print("\nDetailed Sample Cases by Category:")
    for cat_name, items in cats.items():
        print(f"\n--- {cat_name.upper()} (Showing up to 5) ---")
        for i, text in items[:5]:
            print(f"  [{i}] {text[:100]}...")

if __name__ == "__main__":
    main()

