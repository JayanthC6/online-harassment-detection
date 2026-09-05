#!/usr/bin/env python3
"""
scripts/build_test_split.py
───────────────────────────────────────────────────────────────────────────────
Reconstruct the held-out test split used to train and report metrics for
the ShieldAI DistilBERT multi-label classifier, then verify it by running
the production model against it.

WHAT THIS SCRIPT DOES
  1. Downloads / loads the three source datasets in the exact order used in
     the original Colab training notebook:
       (1) Jigsaw Toxic Comment Classification Challenge  ← Kaggle
       (2) HateXplain                                     ← HuggingFace Hub
       (3) OLID (OffensEval 2019)                         ← HuggingFace Hub
  2. Applies the exact same label-mapping rules from the notebook.
  3. Runs iterative_train_test_split with np.random.seed(42) — identical
     call sequence to the training notebook — to recover X_test / y_test.
  4. Saves X_test, y_test, X_texts_test to data/processed/test_unified.npz.
  5. Writes a pinned metadata JSON alongside the .npz so the split is
     reproducible and auditable going forward.
  6. Loads the production HF model (Jayant62003/shieldai-distilbert-multilabel)
     with calibrated thresholds and runs batch inference on the test set.
  7. Computes macro F1, micro F1, and per-category P/R/F1.
  8. Compares against the previously reported numbers (~0.77 macro, ~0.93 micro).
     * If numbers land within +/-0.03 -> split is VERIFIED, safe to use.
     * If outside +/-0.03 -> DISCREPANCY REPORTED. Script prints a clear warning
       and saves actual vs. reported numbers to the metadata file.
       Do NOT substitute the new numbers for the old ones in any public-facing
       document without explicit human sign-off.

PREREQUISITES
  pip install scikit-multilearn datasets huggingface_hub transformers torch \
              scikit-learn pandas numpy requests kaggle python-dotenv

  Environment variables required:
    KAGGLE_API_TOKEN  -- Kaggle API token JSON string  (or ~/.kaggle/kaggle.json)
    HF_TOKEN          -- HuggingFace access token

  Kaggle competition rules must be accepted before running:
    https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge

USAGE
  # From the repo root:
  python scripts/build_test_split.py

  # Skip model verification (split only):
  python scripts/build_test_split.py --no-verify

  # Run verification against an already-built split:
  python scripts/build_test_split.py --verify-only

  # Supply a local Jigsaw zip if you already downloaded it:
  python scripts/build_test_split.py --jigsaw-zip /path/to/jigsaw.zip
"""

import argparse
import json
import os
import sys
import time
import zipfile
import subprocess
import importlib
import warnings
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR      = REPO_ROOT / "data" / "processed"
OUTPUT_NPZ    = DATA_DIR / "test_unified.npz"
METADATA_JSON = DATA_DIR / "test_split_metadata.json"
BACKEND_DIR   = REPO_ROOT / "backend"

# Add backend to sys.path so we can import production modules
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ── Constants (mirror the training notebook exactly) ──────────────────────────
LABELS = [
    "Hate Speech",
    "Cyberbullying / Harassment",
    "Threat",
    "Toxicity / Offensive Language",
    "Profanity",
    "Clean",
]
NUM_LABELS  = len(LABELS)
RANDOM_SEED = 42

# Previously reported numbers — do not change without human decision
REPORTED_MACRO_F1       = 0.77
REPORTED_MICRO_F1       = 0.93
VERIFICATION_TOLERANCE  = 0.03   # +/-3pp considered "close enough"


# ── CLI ────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Reconstruct and verify the ShieldAI test split."
    )
    p.add_argument(
        "--no-verify", action="store_true",
        help="Build and save the split but skip transformer verification."
    )
    p.add_argument(
        "--verify-only", action="store_true",
        help="Skip dataset reconstruction; load existing .npz and run verification only."
    )
    p.add_argument(
        "--jigsaw-zip", type=str, default=None,
        help="Path to an already-downloaded Jigsaw competition zip file."
    )
    p.add_argument(
        "--batch-size", type=int, default=32,
        help="Batch size for transformer inference (default: 32)."
    )
    return p.parse_args()


# ── Dependency / version pinning ──────────────────────────────────────────────
def _pkg_version(name: str) -> str:
    """Return installed version of a package, or 'not_found'."""
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "not_found"


def collect_env_versions() -> dict:
    import numpy
    import pandas
    return {
        "numpy":              numpy.__version__,
        "pandas":             pandas.__version__,
        "scikit_multilearn":  _pkg_version("scikit-multilearn"),
        "datasets":           _pkg_version("datasets"),
        "transformers":       _pkg_version("transformers"),
        "torch":              _pkg_version("torch"),
        "scikit_learn":       _pkg_version("scikit-learn"),
        "huggingface_hub":    _pkg_version("huggingface-hub"),
    }


# ── Logging helpers ────────────────────────────────────────────────────────────
def banner(msg: str):
    print("\n" + "=" * 70)
    print(f"  {msg}")
    print("=" * 70)


def step(msg: str):
    print(f"\n-- {msg}")


def ok(msg: str):
    print(f"   OK: {msg}")


def warn(msg: str):
    print(f"   WARNING: {msg}", file=sys.stderr)


def fail(msg: str):
    print(f"\n{'!'*70}\n  FAILURE: {msg}\n{'!'*70}", file=sys.stderr)
    sys.exit(1)


# ── Dataset loaders ────────────────────────────────────────────────────────────

def _init_row() -> dict:
    return {l: 0 for l in LABELS}


def load_jigsaw(jigsaw_zip_path) -> list:
    """
    Load Jigsaw Toxic Comment Classification Challenge.
    Concatenation order: FIRST in unified_data (rows 0..N-1).
    """
    import pandas as pd

    step("Loading Jigsaw dataset ...")

    tmp_dir = REPO_ROOT / "scripts" / "_jigsaw_tmp"

    if jigsaw_zip_path:
        zip_path = Path(jigsaw_zip_path)
        if not zip_path.exists():
            fail(f"Supplied Jigsaw zip not found: {zip_path}")
    else:
        zip_path = tmp_dir / "jigsaw-toxic-comment-classification-challenge.zip"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        if not zip_path.exists():
            kaggle_token = os.environ.get("KAGGLE_API_TOKEN")
            if kaggle_token:
                kaggle_dir = Path.home() / ".kaggle"
                kaggle_dir.mkdir(exist_ok=True)
                kaggle_json = kaggle_dir / "kaggle.json"
                if not kaggle_json.exists():
                    kaggle_json.write_text(kaggle_token)
                    kaggle_json.chmod(0o600)

            result = subprocess.run(
                [
                    "kaggle", "competitions", "download",
                    "-c", "jigsaw-toxic-comment-classification-challenge",
                    "-p", str(tmp_dir),
                ],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                err = result.stderr.lower() + result.stdout.lower()
                if "401" in err or "unauthorized" in err:
                    fail(
                        "Kaggle auth failed. Ensure KAGGLE_API_TOKEN is set "
                        "or ~/.kaggle/kaggle.json exists."
                    )
                elif "403" in err or "forbidden" in err:
                    fail(
                        "Kaggle 403 — accept competition rules at:\n"
                        "  https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge"
                    )
                else:
                    fail(f"Kaggle download failed:\n{result.stderr}")

    extract_dir = tmp_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    ok(f"Extracting from {zip_path} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # The competition zip contains train.csv.zip inside
    inner_zip = extract_dir / "train.csv.zip"
    if inner_zip.exists():
        with zipfile.ZipFile(inner_zip, "r") as zf:
            zf.extractall(extract_dir)
        csv_path = extract_dir / "train.csv"
    else:
        csv_path = extract_dir / "train.csv"
        if not csv_path.exists():
            candidates = list(extract_dir.glob("**/*.csv"))
            if not candidates:
                fail(f"Could not find train.csv in {extract_dir}")
            csv_path = candidates[0]
            warn(f"Using fallback CSV: {csv_path}")

    jigsaw_df = pd.read_csv(csv_path)
    ok(f"Jigsaw loaded: {len(jigsaw_df):,} rows")

    rows = []
    for _, row in jigsaw_df.iterrows():
        new_row = _init_row()
        new_row["text"] = str(row["comment_text"])

        # Exact mapping from notebook
        if row.get("toxic", 0) == 1 or row.get("severe_toxic", 0) == 1:
            new_row["Toxicity / Offensive Language"] = 1
        if row.get("obscene", 0) == 1:
            new_row["Profanity"] = 1
        if row.get("threat", 0) == 1:
            new_row["Threat"] = 1
        if row.get("insult", 0) == 1:
            new_row["Cyberbullying / Harassment"] = 1
        if row.get("identity_hate", 0) == 1:
            new_row["Hate Speech"] = 1

        if sum(new_row[k] for k in LABELS if k != "Clean") == 0:
            new_row["Clean"] = 1

        rows.append(new_row)

    ok(f"Jigsaw mapped: {len(rows):,} rows added to unified_data")
    return rows


def load_hatexplain() -> list:
    """
    Load HateXplain. Tries HF parquet first, falls back to GitHub JSON.
    Concatenation order: SECOND (after Jigsaw).
    """
    step("Loading HateXplain dataset ...")
    rows = []

    def _from_parquet(hx_row):
        new_row = _init_row()
        new_row["text"] = " ".join(hx_row["post_tokens"])
        ann = hx_row["annotators"]
        labels_list = ann["label"] if isinstance(ann, dict) else [a["label"] for a in ann]
        majority = max(set(labels_list), key=labels_list.count)
        if majority == 0:
            new_row["Hate Speech"] = 1
        elif majority == 2:
            new_row["Toxicity / Offensive Language"] = 1
        elif majority == 1:
            new_row["Clean"] = 1
        return new_row

    def _from_github(hx_row):
        new_row = _init_row()
        new_row["text"] = " ".join(hx_row["post_tokens"])
        labels_list = [a["label"] for a in hx_row["annotators"]]
        majority = max(set(labels_list), key=labels_list.count)
        if majority == "hatespeech":
            new_row["Hate Speech"] = 1
        elif majority == "offensive":
            new_row["Toxicity / Offensive Language"] = 1
        elif majority == "normal":
            new_row["Clean"] = 1
        return new_row

    try:
        from datasets import load_dataset
        hx = load_dataset("hatexplain", revision="refs/convert/parquet", split="train")
        for hx_row in hx:
            rows.append(_from_parquet(hx_row))
        ok(f"HateXplain (parquet) loaded: {len(rows):,} rows added to unified_data")
    except Exception as e:
        warn(f"HateXplain parquet failed ({e}). Falling back to GitHub JSON ...")
        try:
            import requests
            resp = requests.get(
                "https://raw.githubusercontent.com/hate-alert/HateXplain/master/Data/dataset.json",
                timeout=60,
            )
            resp.raise_for_status()
            hx_data = resp.json()
            for post_id, hx_row in hx_data.items():
                rows.append(_from_github(hx_row))
            ok(f"HateXplain (GitHub JSON) loaded: {len(rows):,} rows added to unified_data")
        except Exception as e2:
            fail(
                f"Both HateXplain load paths failed.\n"
                f"  Parquet error: {e}\n"
                f"  GitHub error:  {e2}"
            )

    return rows


def load_olid() -> list:
    """
    Load OLID from HuggingFace Hub.
    Concatenation order: THIRD (after HateXplain).
    """
    step("Loading OLID (OffensEval 2019) ...")
    rows = []

    try:
        import pandas as pd
        from huggingface_hub import hf_hub_download

        olid_path = hf_hub_download(
            repo_id="christophsonntag/OLID",
            filename="data/olid-training-v1.0.tsv",
            repo_type="dataset",
        )
        olid_df = pd.read_csv(olid_path, sep="\t", na_values=["NULL"])
        ok(f"OLID loaded: {len(olid_df):,} rows  columns={olid_df.columns.tolist()}")

        for _, row in olid_df.iterrows():
            new_row = _init_row()
            new_row["text"] = str(row["tweet"])

            is_off = row.get("subtask_a") == "OFF"
            is_tin = row.get("subtask_b") == "TIN"
            is_grp = row.get("subtask_c") == "GRP"

            if is_off:
                new_row["Toxicity / Offensive Language"] = 1
            if is_off and is_tin:
                new_row["Cyberbullying / Harassment"] = 1
            if is_off and is_tin and is_grp:
                new_row["Hate Speech"] = 1
            if not is_off:
                new_row["Clean"] = 1

            rows.append(new_row)

        ok(f"OLID mapped: {len(rows):,} rows added to unified_data")

    except Exception as e:
        fail(f"Failed to load OLID from HF Hub: {e}")

    return rows


# ── Split reconstruction ────────────────────────────────────────────────────────

def build_split(jigsaw_zip_path) -> tuple:
    """
    Reconstruct the exact split. Returns (X_test_texts, y_test, split_metadata).
    """
    import numpy as np
    import pandas as pd

    # Concatenation order: JIGSAW first, HATEXPLAIN second, OLID third
    jigsaw_rows       = load_jigsaw(jigsaw_zip_path)
    hatexplain_rows   = load_hatexplain()
    olid_rows         = load_olid()

    concatenation_order = ["Jigsaw", "HateXplain", "OLID"]
    source_sizes = {
        "Jigsaw":     len(jigsaw_rows),
        "HateXplain": len(hatexplain_rows),
        "OLID":       len(olid_rows),
    }

    unified_data = jigsaw_rows + hatexplain_rows + olid_rows
    df = pd.DataFrame(unified_data)

    banner(f"Unified dataset: {len(df):,} total rows")
    for label in LABELS:
        count = int(df[label].sum())
        print(f"   {label:<38} {count:>6,} positive examples")

    step("Running iterative stratified split (seed=42) ...")

    try:
        from skmultilearn.model_selection import iterative_train_test_split
    except ImportError:
        fail("scikit-multilearn not installed.  pip install scikit-multilearn")

    X = df["text"].values.reshape(-1, 1)
    y = df[LABELS].values.astype(int)

    # Seed set immediately before first split — mirrors notebook exactly
    np.random.seed(RANDOM_SEED)

    # Split 1: 80% train, 20% temp
    X_train, y_train, X_temp, y_temp = iterative_train_test_split(X, y, test_size=0.2)
    # Split 2: 50/50 of temp -> 10% val, 10% test
    X_val, y_val, X_test, y_test = iterative_train_test_split(X_temp, y_temp, test_size=0.5)

    X_test_texts = [x[0] for x in X_test]
    y_test_array = y_test.astype(int)

    banner(
        f"Split sizes: train={len(X_train):,}  "
        f"val={len(X_val):,}  test={len(X_test_texts):,}"
    )

    step("Test set label distribution:")
    for i, label in enumerate(LABELS):
        pos = int(y_test_array[:, i].sum())
        pct = 100.0 * pos / len(y_test_array)
        print(f"   {label:<38} {pos:>5,}  ({pct:.1f}%)")

    split_metadata = {
        "concatenation_order":    concatenation_order,
        "source_sizes":           source_sizes,
        "total_unified_rows":     int(len(df)),
        "split_sizes": {
            "train": int(len(X_train)),
            "val":   int(len(X_val)),
            "test":  int(len(X_test_texts)),
        },
        "random_seed":            RANDOM_SEED,
        "split_strategy":         "skmultilearn.model_selection.iterative_train_test_split",
        "split_call_sequence": [
            "np.random.seed(42)",
            "X_train, y_train, X_temp, y_temp = iterative_train_test_split(X, y, test_size=0.2)",
            "X_val, y_val, X_test, y_test = iterative_train_test_split(X_temp, y_temp, test_size=0.5)",
        ],
        "label_order": LABELS,
        "test_label_positive_counts": {
            label: int(y_test_array[:, i].sum())
            for i, label in enumerate(LABELS)
        },
    }

    return X_test_texts, y_test_array, split_metadata


# ── Persist ────────────────────────────────────────────────────────────────────

def save_split(X_test_texts: list, y_test_array, split_metadata: dict, env_versions: dict) -> dict:
    import numpy as np

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    step(f"Saving test split -> {OUTPUT_NPZ} ...")
    np.savez_compressed(
        OUTPUT_NPZ,
        X_test=np.array(X_test_texts, dtype=object),
        y_test=y_test_array,
    )
    ok(f"Saved {OUTPUT_NPZ.name}  ({OUTPUT_NPZ.stat().st_size / 1024:.1f} KB)")

    metadata = {
        "generated_at_utc":        datetime.now(timezone.utc).isoformat(),
        "script":                  "scripts/build_test_split.py",
        "label_mapping_source":    "notebooks/ShieldAI_MultiLabel_FineTuning.ipynb",
        "split":                   split_metadata,
        "env_versions":            env_versions,
        "verification":            None,   # filled in after model run
    }

    METADATA_JSON.write_text(json.dumps(metadata, indent=2))
    ok(f"Saved {METADATA_JSON.name}")
    return metadata


def load_split_from_disk() -> tuple:
    import numpy as np

    if not OUTPUT_NPZ.exists():
        fail(
            f"No saved split at {OUTPUT_NPZ}.\n"
            "Run without --verify-only first."
        )
    step(f"Loading split from {OUTPUT_NPZ} ...")
    data = np.load(OUTPUT_NPZ, allow_pickle=True)
    X_test_texts = list(data["X_test"])
    y_test_array = data["y_test"].astype(int)
    ok(f"Loaded {len(X_test_texts):,} examples  y_test shape={y_test_array.shape}")
    return X_test_texts, y_test_array


# ── Transformer verification ────────────────────────────────────────────────────

def batch_predict_transformer(texts: list, batch_size: int, device, model, tokenizer, thresholds) -> tuple:
    """
    Batched inference. Returns (y_pred_binary, y_probs) both shape (N, NUM_LABELS).
    Label column order matches LABELS list.
    """
    import numpy as np
    import torch

    # Reproduce the id2label remapping from predict_transformer.py
    id2label = model.config.id2label
    if id2label and "LABEL_0" in id2label.values():
        id2label = {
            0: "Hate Speech",
            1: "Cyberbullying / Harassment",
            2: "Threat",
            3: "Toxicity / Offensive Language",
            4: "Profanity",
            5: "Clean",
        }

    all_probs = []
    n = len(texts)
    t0 = time.time()

    for batch_start in range(0, n, batch_size):
        batch_texts = texts[batch_start: batch_start + batch_size]
        inputs = tokenizer(
            batch_texts,
            truncation=True,
            padding=True,
            max_length=256,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
            probs_batch = torch.sigmoid(logits).cpu().numpy()

        all_probs.append(probs_batch)

        done    = min(batch_start + batch_size, n)
        elapsed = time.time() - t0
        pct     = done / n
        eta     = (elapsed / pct) * (1 - pct) if pct > 0 else 0
        print(
            f"\r   Inference: {done:>6,}/{n:,}  ({100*pct:.1f}%)  ETA {eta:.0f}s   ",
            end="", flush=True,
        )

    print()
    all_probs = __import__("numpy").vstack(all_probs)  # (N, num_labels)

    # Apply calibrated thresholds in LABELS order
    y_pred = __import__("numpy").zeros_like(all_probs, dtype=int)
    for i, label in enumerate(LABELS):
        # Find column index in the model output that matches this label
        col_idx = next((k for k, v in id2label.items() if v == label), i)
        thresh  = thresholds.get(label, 0.5)
        y_pred[:, i] = (all_probs[:, col_idx] >= thresh).astype(int)

    return y_pred, all_probs


def run_verification(X_test_texts: list, y_test_array, batch_size: int) -> dict:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")

    import ml.predict_transformer as pt

    banner("Verification: Running production transformer on reconstructed test set")

    if not pt.is_available():
        warn("HF_TOKEN not set or torch/transformers missing — skipping verification.")
        return {
            "status": "SKIPPED",
            "reason": "HF_TOKEN missing or torch/transformers not installed",
        }

    step("Loading model from HuggingFace Hub ...")
    model, tokenizer, thresholds, device = pt._load()
    ok(f"Device: {device}")
    ok(f"Calibrated thresholds: {thresholds}")

    step(f"Running batched inference (batch_size={batch_size}) on {len(X_test_texts):,} examples ...")
    y_pred, y_probs = batch_predict_transformer(
        X_test_texts, batch_size, device, model, tokenizer, thresholds
    )

    from sklearn.metrics import f1_score, precision_score, recall_score

    macro_f1 = float(f1_score(y_test_array, y_pred, average="macro",  zero_division=0))
    micro_f1 = float(f1_score(y_test_array, y_pred, average="micro",  zero_division=0))

    per_label = {}
    for i, label in enumerate(LABELS):
        p = float(precision_score(y_test_array[:, i], y_pred[:, i], zero_division=0))
        r = float(recall_score(y_test_array[:, i],    y_pred[:, i], zero_division=0))
        f = float(f1_score(y_test_array[:, i],         y_pred[:, i], zero_division=0))
        per_label[label] = {"precision": round(p,4), "recall": round(r,4), "f1": round(f,4)}

    # ── Print results ──────────────────────────────────────────────────────
    banner("Transformer-only results on reconstructed test set")
    print(f"\n   Macro F1 : {macro_f1:.4f}   (previously reported: ~{REPORTED_MACRO_F1})")
    print(f"   Micro F1 : {micro_f1:.4f}   (previously reported: ~{REPORTED_MICRO_F1})")
    print()
    print(f"   {'Category':<38}  {'Prec':>6}  {'Rec':>6}  {'F1':>6}")
    print(f"   {'─'*38}  {'─'*6}  {'─'*6}  {'─'*6}")
    for label, m in per_label.items():
        flag = "  <- F1 < 0.5" if m["f1"] < 0.5 else ""
        print(
            f"   {label:<38}  {m['precision']:>6.4f}  "
            f"{m['recall']:>6.4f}  {m['f1']:>6.4f}{flag}"
        )

    # ── Verification decision ──────────────────────────────────────────────
    macro_delta = abs(macro_f1 - REPORTED_MACRO_F1)
    micro_delta = abs(micro_f1 - REPORTED_MICRO_F1)
    verified    = macro_delta <= VERIFICATION_TOLERANCE and micro_delta <= VERIFICATION_TOLERANCE

    result = {
        "status":             "VERIFIED" if verified else "DISCREPANCY",
        "computed_macro_f1":  round(macro_f1, 4),
        "computed_micro_f1":  round(micro_f1, 4),
        "reported_macro_f1":  REPORTED_MACRO_F1,
        "reported_micro_f1":  REPORTED_MICRO_F1,
        "macro_delta":        round(macro_delta, 4),
        "micro_delta":        round(micro_delta, 4),
        "tolerance":          VERIFICATION_TOLERANCE,
        "per_label_metrics":  per_label,
        "per_label_f1":       {label: m["f1"] for label, m in per_label.items()},
        "categories_below_f1_0.5": [
            label for label, m in per_label.items() if m["f1"] < 0.5
        ],
    }

    banner("VERIFICATION RESULT")

    if verified:
        print(
            f"   VERIFIED\n"
            f"   Reconstructed split produces metrics consistent with previously\n"
            f"   reported numbers (within +/-{VERIFICATION_TOLERANCE}).\n"
            f"   macro delta={macro_delta:.4f}  micro delta={micro_delta:.4f}\n\n"
            f"   The test split at {OUTPUT_NPZ.name} is safe to use for the\n"
            f"   3-way benchmark (symbolic / transformer / fusion)."
        )
    else:
        print(
            f"   DISCREPANCY DETECTED\n"
            f"\n"
            f"   The reconstructed split produces numbers that differ from the\n"
            f"   previously reported values by more than +/-{VERIFICATION_TOLERANCE}:\n"
            f"\n"
            f"     Metric       Reported   Computed   Delta\n"
            f"     ─────────── ─────────  ─────────  ──────\n"
            f"     Macro F1    {REPORTED_MACRO_F1:.4f}     {macro_f1:.4f}     {macro_delta:+.4f}\n"
            f"     Micro F1    {REPORTED_MICRO_F1:.4f}     {micro_f1:.4f}     {micro_delta:+.4f}\n"
            f"\n"
            f"   Possible causes:\n"
            f"   1. HateXplain parquet vs JSON fallback changed the label distribution\n"
            f"   2. OLID subtask_b/c NaN handling differs from original Colab run\n"
            f"   3. scikit-multilearn version difference altered iterative split order\n"
            f"   4. The original reported numbers came from a different dataset state\n"
            f"\n"
            f"   ACTION REQUIRED:\n"
            f"   - Do NOT update README, docs, or any public claim with the computed\n"
            f"     numbers without explicit human review and sign-off.\n"
            f"   - Discrepancy is logged in: {METADATA_JSON.name}\n"
            f"   - Investigate the causes listed above, then re-run this script.",
            file=sys.stderr,
        )

    if result["categories_below_f1_0.5"]:
        print(
            f"\n   Categories where transformer-only F1 < 0.5\n"
            f"   (confirm whether fusion helps each in the 3-way benchmark):"
        )
        for label in result["categories_below_f1_0.5"]:
            print(f"     * {label}  (F1 = {per_label[label]['f1']:.4f})")

    return result


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    banner("ShieldAI -- Test Split Reconstruction & Verification")
    print(f"   Repo root : {REPO_ROOT}")
    print(f"   Output    : {OUTPUT_NPZ}")
    print(f"   Metadata  : {METADATA_JSON}")

    env_versions = collect_env_versions()
    step("Pinned dependency versions:")
    for pkg, ver in env_versions.items():
        print(f"   {pkg:<25} {ver}")

    # ── Phase 1: Build or load ─────────────────────────────────────────────
    if args.verify_only:
        X_test_texts, y_test_array = load_split_from_disk()
        metadata = (
            json.loads(METADATA_JSON.read_text())
            if METADATA_JSON.exists()
            else {"generated_at_utc": None, "split": {}, "env_versions": env_versions, "verification": None}
        )
    else:
        X_test_texts, y_test_array, split_metadata = build_split(args.jigsaw_zip)
        metadata = save_split(X_test_texts, y_test_array, split_metadata, env_versions)

    # ── Phase 2: Verify ────────────────────────────────────────────────────
    if args.no_verify:
        step("Skipping transformer verification (--no-verify).")
        print(f"\n   To verify later:  python scripts/build_test_split.py --verify-only")
        return

    verification = run_verification(X_test_texts, y_test_array, args.batch_size)

    # Persist verification into metadata JSON
    metadata["verification"] = {
        "verified_at_utc":               datetime.now(timezone.utc).isoformat(),
        "model_repo":                    "Jayant62003/shieldai-distilbert-multilabel",
        "env_versions_at_verification":  env_versions,
        **verification,
    }
    METADATA_JSON.write_text(json.dumps(metadata, indent=2))
    ok(f"Metadata updated with verification result -> {METADATA_JSON.name}")

    if verification.get("status") == "DISCREPANCY":
        sys.exit(1)   # non-zero so CI pipelines catch it


if __name__ == "__main__":
    main()
