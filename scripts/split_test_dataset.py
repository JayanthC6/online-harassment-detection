"""
Split backend/data/test.csv into disjoint stratified halves:
- backend/data/tune.csv
- backend/data/final.csv
Fixed seed = 42.
"""
import os
import pandas as pd
import numpy as np

BACKEND_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data")
TEST_CSV_PATH = os.path.join(BACKEND_DATA_DIR, "test.csv")
TUNE_CSV_PATH = os.path.join(BACKEND_DATA_DIR, "tune.csv")
FINAL_CSV_PATH = os.path.join(BACKEND_DATA_DIR, "final.csv")

LABEL_ORDER = [
    "Hate Speech",
    "Cyberbullying / Harassment",
    "Threat",
    "Toxicity / Offensive Language",
    "Profanity",
    "Clean"
]

def split_dataset():
    df = pd.read_csv(TEST_CSV_PATH)
    df["strata"] = df[LABEL_ORDER].astype(str).agg("".join, axis=1)

    rng = np.random.RandomState(42)
    tune_indices = []
    final_indices = []

    groups = df.groupby("strata", sort=False)
    odd_toggle = 0

    for strata_val, group in groups:
        indices = group.index.values.copy()
        rng.shuffle(indices)
        n = len(indices)
        half = n // 2
        if n % 2 == 0:
            tune_indices.extend(indices[:half])
            final_indices.extend(indices[half:])
        else:
            if odd_toggle % 2 == 0:
                tune_indices.extend(indices[:half + 1])
                final_indices.extend(indices[half + 1:])
            else:
                tune_indices.extend(indices[:half])
                final_indices.extend(indices[half:])
            odd_toggle += 1

    tune_df = df.loc[tune_indices].drop(columns=["strata"]).sample(frac=1.0, random_state=42).reset_index(drop=True)
    final_df = df.loc[final_indices].drop(columns=["strata"]).sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Disjointness assertions
    assert len(tune_df) + len(final_df) == len(df), "Row counts do not match total"
    overlap = set(tune_df["text"]).intersection(set(final_df["text"]))
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping texts between tune and final!"

    tune_df.to_csv(TUNE_CSV_PATH, index=False)
    final_df.to_csv(FINAL_CSV_PATH, index=False)
    print(f"Saved {TUNE_CSV_PATH} ({len(tune_df)} rows)")
    print(f"Saved {FINAL_CSV_PATH} ({len(final_df)} rows)")

    print("\nVerification & Per-Label Support:")
    print(f"{'Label':<32} {'Tune Support':<14} {'Final Support':<14} {'Total Support':<14}")
    print("-" * 74)
    for l in LABEL_ORDER:
        t_sup = int(tune_df[l].sum())
        f_sup = int(final_df[l].sum())
        tot_sup = int(df[l].sum())
        print(f"{l:<32} {t_sup:<14} {f_sup:<14} {tot_sup:<14}")
    print("-" * 74)
    print(f"{'Total Row Count':<32} {len(tune_df):<14} {len(final_df):<14} {len(df):<14}")

if __name__ == "__main__":
    split_dataset()

