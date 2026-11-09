"""
ShieldAI Model & Detection Engine Evaluation Harness.

Evaluates two architectures on the held-out test dataset:
  (a) DistilBERT Neural Model Alone (with calibrated decision thresholds from thresholds.json)
  (b) Full Hybrid Detection Engine (DistilBERT + Heuristics, Hinglish Rules, and Threat Intel)

Computes per-label Precision, Recall, F1-Score, Macro/Micro Averages, and 2x2 Confusion Matrices.

Usage:
    python scripts/evaluate_model.py [--csv PATH] [--batch-size N] [--allow-small]
"""

import os
import sys
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

# Ensure backend directory is in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

DEFAULT_CSV_PATH = os.path.join(BACKEND_DIR, "data", "test.csv")
MIN_REQUIRED_ROWS = 500
LABEL_ORDER = [
    "Hate Speech",
    "Cyberbullying / Harassment",
    "Threat",
    "Toxicity / Offensive Language",
    "Profanity",
    "Clean"
]


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, labels: list):
    """Computes Precision, Recall, F1, Support, Macro/Micro averages, and 2x2 Confusion Matrices."""
    precisions = []
    recalls = []
    f1s = []
    supports = []
    cms = {}

    for idx, label in enumerate(labels):
        yt = y_true[:, idx]
        yp = y_pred[:, idx]

        tp = int(np.sum((yt == 1) & (yp == 1)))
        fp = int(np.sum((yt == 0) & (yp == 1)))
        fn = int(np.sum((yt == 1) & (yp == 0)))
        tn = int(np.sum((yt == 0) & (yp == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        support = int(np.sum(yt == 1))

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)
        supports.append(support)
        cms[label] = [[tn, fp], [fn, tp]]

    macro_prec = float(np.mean(precisions))
    macro_rec = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))

    # Also compute 5 abuse labels (excluding 'Clean' if present)
    if "Clean" in labels:
        clean_idx = labels.index("Clean")
        abuse_p = [p for i, p in enumerate(precisions) if i != clean_idx]
        abuse_r = [r for i, r in enumerate(recalls) if i != clean_idx]
        abuse_f = [f for i, f in enumerate(f1s) if i != clean_idx]
        macro_5_prec = float(np.mean(abuse_p))
        macro_5_rec = float(np.mean(abuse_r))
        macro_5_f1 = float(np.mean(abuse_f))
    else:
        macro_5_prec, macro_5_rec, macro_5_f1 = macro_prec, macro_rec, macro_f1

    micro_tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    micro_fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    micro_fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    micro_prec = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0
    micro_rec = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec) if (micro_prec + micro_rec) > 0 else 0.0

    return {
        "labels": labels,
        "precisions": precisions,
        "recalls": recalls,
        "f1s": f1s,
        "supports": supports,
        "macro": (macro_prec, macro_rec, macro_f1),
        "macro_5": (macro_5_prec, macro_5_rec, macro_5_f1),
        "micro": (micro_prec, micro_rec, micro_f1),
        "cms": cms,
        "total_positives": int(np.sum(y_true == 1))
    }


def print_evaluation_table(title: str, results: dict):
    """Renders formatted evaluation table and 2x2 confusion matrices."""
    print("\n" + "=" * 82)
    print(title)
    print("=" * 82)
    print(f"{'Label':<32} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<8}")
    print("-" * 82)

    for i, label in enumerate(results["labels"]):
        p = results["precisions"][i]
        r = results["recalls"][i]
        f = results["f1s"][i]
        s = results["supports"][i]
        print(f"{label:<32} {p:<12.4f} {r:<12.4f} {f:<12.4f} {s:<8}")

    print("-" * 82)
    m5p, m5r, m5f = results["macro_5"]
    mp, mr, mf = results["macro"]
    u_p, u_r, u_f = results["micro"]
    tot = results["total_positives"]
    print(f"{'Macro Avg (5 Abuse Labels)':<32} {m5p:<12.4f} {m5r:<12.4f} {m5f:<12.4f} {'(Abuse)'}")
    print(f"{'Macro Avg (All 6 Labels)':<32} {mp:<12.4f} {mr:<12.4f} {mf:<12.4f} {tot:<8}")
    print(f"{'Micro Average':<32} {u_p:<12.4f} {u_r:<12.4f} {u_f:<12.4f} {tot:<8}")
    print("=" * 82)

    print("\nPER-LABEL 2x2 CONFUSION MATRICES (Format: [[TN, FP], [FN, TP]]):")
    print("-" * 82)
    for label in results["labels"]:
        cm = results["cms"][label]
        print(f"\nLabel: {label}")
        print("  Predicted 0 (Neg)  Predicted 1 (Pos)")
        print(f"Actual 0:    TN = {cm[0][0]:<6}    FP = {cm[0][1]:<6}")
        print(f"Actual 1:    FN = {cm[1][0]:<6}    TP = {cm[1][1]:<6}")


def evaluate(csv_path: str, batch_size: int = 64, allow_small: bool = False):
    abs_path = os.path.abspath(csv_path)

    print("=" * 82)
    print(">>> SHIELDAI EVALUATION HARNESS: HELD-OUT TEST BENCHMARK")
    print("=" * 82)

    if not os.path.exists(abs_path):
        print(f"\n[ERROR] Dataset not found at: {abs_path}")
        print("Please place the real held-out test.csv dataset file in backend/data/ and re-run.")
        sys.exit(1)

    mtime = datetime.fromtimestamp(os.path.getmtime(abs_path)).strftime("%Y-%m-%d %H:%M:%S")
    file_size_kb = os.path.getsize(abs_path) / 1024.0

    try:
        df = pd.read_csv(abs_path)
    except Exception as e:
        print(f"\n[ERROR] Failed to parse CSV at {abs_path}: {e}")
        sys.exit(1)

    row_count = len(df)

    print(f"Dataset path:            {abs_path}")
    print(f"File modification time:  {mtime}")
    print(f"File size:               {file_size_kb:.2f} KB")
    print(f"Total row count:         {row_count}")
    print("=" * 82)

    # Enforce minimum 500 rows constraint
    if row_count < MIN_REQUIRED_ROWS and not allow_small:
        print(f"\n[ERROR] Dataset contains only {row_count} rows.")
        print(f"A minimum of {MIN_REQUIRED_ROWS} rows is required for statistically valid held-out evaluation.")
        print("To override this guard and evaluate a smaller development set, pass '--allow-small':")
        print(f"    python scripts/evaluate_model.py --allow-small --csv \"{csv_path}\"")
        sys.exit(1)

    # Validate column structure
    required_cols = ["text"] + LABEL_ORDER
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"\n[ERROR] CSV is missing required columns: {missing_cols}")
        print(f"Expected schema: 'text', {', '.join(LABEL_ORDER)}")
        sys.exit(1)

    # Late import of ModelService only after validation passes
    from services.model_service import ModelService

    service = ModelService.get_instance()
    if not service.is_loaded:
        print("\n[ERROR] DistilBERT model weights not loaded. Verify backend/models/shieldai path.")
        sys.exit(1)

    texts = df["text"].astype(str).tolist()
    y_true = df[LABEL_ORDER].astype(int).values

    print("\nActive Calibrated Decision Thresholds (thresholds.json):")
    for label in LABEL_ORDER:
        t = service.thresholds.get(label, 0.5)
        print(f"  * {label:<32} threshold = {t:.4f}")

    # ─────────────────────────────────────────────────────────────────────────
    # EVALUATION (a): DistilBERT Model Alone (with thresholds.json)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[1/2] Running inference: DistilBERT Model Alone across {row_count} items (batch size: {batch_size})...", flush=True)
    import time
    import pickle
    import torch
    t0_inf = time.time()

    file_cache = os.path.join(BACKEND_DIR, "data", f".model_inf_cache_{os.path.basename(csv_path)}.pkl")
    global_cache = os.path.join(BACKEND_DIR, "data", ".model_inf_cache.pkl")
    test_csv_path = os.path.join(BACKEND_DIR, "data", "test.csv")
    raw_model_results = None
    y_pred_model = None

    if os.path.exists(file_cache):
        try:
            with open(file_cache, "rb") as f:
                cached_data = pickle.load(f)
                if (
                    len(cached_data.get("raw_model_results", [])) == len(texts) and
                    len(cached_data.get("y_pred_model", [])) == len(texts)
                ):
                    raw_model_results = cached_data["raw_model_results"]
                    y_pred_model = np.array(cached_data["y_pred_model"])
                    print(f"  [CACHE] Loaded precomputed neural predictions for all {row_count} items from {os.path.basename(file_cache)}!", flush=True)
        except Exception:
            pass

    if raw_model_results is None and os.path.exists(global_cache) and os.path.exists(test_csv_path):
        try:
            with open(global_cache, "rb") as f:
                g_data = pickle.load(f)
            t_df = pd.read_csv(test_csv_path)
            if len(t_df) == len(g_data.get("raw_model_results", [])):
                t_map = {t: (r, p) for t, r, p in zip(t_df["text"].astype(str), g_data["raw_model_results"], g_data["y_pred_model"])}
                if all(t in t_map for t in texts):
                    raw_model_results = [t_map[t][0] for t in texts]
                    y_pred_model = np.array([t_map[t][1] for t in texts])
                    print(f"  [CACHE] Resolved precomputed neural predictions for all {row_count} items from global cache!", flush=True)
                    try:
                        with open(file_cache, "wb") as f_out:
                            pickle.dump({"raw_model_results": raw_model_results, "y_pred_model": y_pred_model}, f_out)
                    except Exception:
                        pass
        except Exception:
            pass

    if raw_model_results is None or y_pred_model is None:
        # Sort indices by text length for dynamic padding efficiency, preserving original mapping
        sorted_indices = sorted(range(len(texts)), key=lambda k: len(texts[k]))
        raw_model_results = [None] * len(texts)
        y_pred_model_list = [None] * len(texts)

        total_batches = (len(texts) + batch_size - 1) // batch_size
        for b_idx in range(total_batches):
            start_k = b_idx * batch_size
            end_k = min(start_k + batch_size, len(texts))
            batch_orig_idx = sorted_indices[start_k:end_k]
            batch_texts = [texts[k] for k in batch_orig_idx]

            inputs = service.tokenizer(
                batch_texts,
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors="pt"
            )
            inputs = {k: v.to(service.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = service.model(**inputs).logits
                probs_tensor = torch.sigmoid(logits).cpu().numpy()

            for row_i, orig_i in enumerate(batch_orig_idx):
                row_probs = probs_tensor[row_i]
                probs_map = {}
                scores_map = {}
                row_preds = []

                for l_idx, l_name in enumerate(LABEL_ORDER):
                    p = float(row_probs[l_idx])
                    thresh = service.thresholds.get(l_name, 0.5)
                    probs_map[l_name] = round(p, 4)
                    scores_map[l_name] = service.probability_to_relative_score(p, thresh)
                    row_preds.append(1 if p >= thresh else 0)

                raw_model_results[orig_i] = {
                    "probs": probs_map,
                    "scores": scores_map,
                    "active": True
                }
                y_pred_model_list[orig_i] = row_preds

            if (b_idx + 1) % 25 == 0 or (b_idx + 1) == total_batches:
                processed = end_k
                pct = (processed / len(texts)) * 100
                elapsed = time.time() - t0_inf
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (len(texts) - processed) / rate if rate > 0 else 0
                print(f"  Progress: {processed}/{len(texts)} rows ({pct:.1f}%) processed [{rate:.1f} rows/s, ETA: {eta:.0f}s]", flush=True)

        y_pred_model = np.array(y_pred_model_list)
        try:
            with open(cache_file, "wb") as f:
                pickle.dump({"raw_model_results": raw_model_results, "y_pred_model": y_pred_model}, f)
        except Exception:
            pass

    res_model_alone = calculate_metrics(y_true, y_pred_model, LABEL_ORDER)
    print_evaluation_table("EVALUATION (a): DISTILBERT MODEL ALONE (WITH THRESHOLDS.JSON)", res_model_alone)

    # ─────────────────────────────────────────────────────────────────────────
    # EVALUATION (b): Full Hybrid Detection Engine (Model + Rules + Threat Intel)
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n[2/2] Running inference: Full Hybrid Detection Engine across {row_count} items...", flush=True)
    t0_hyb = time.time()
    y_pred_hybrid = []

    for idx, text in enumerate(texts):
        m_res = raw_model_results[idx]
        analysis = service.analyze(text, precomputed_model_res=m_res)
        cat_scores = analysis.get("category_scores", {})
        overall_score = analysis.get("score", 0.0)
        signals = analysis.get("signals", [])

        # Map hybrid detection output into the 6 trained taxonomy labels
        # 1. Hate Speech: model threshold OR rule signals for hate speech / racism
        has_hate_signal = any(
            s.get("category") == "harassment" and any(k in s.get("signal", "").lower() for k in ["hate speech", "racis", "religion", "slur"])
            for s in signals
        )
        is_hate = 1 if (y_pred_model[idx, 0] == 1 or has_hate_signal) else 0

        # 2. Cyberbullying / Harassment: model harassment OR sextortion >= 50 OR Hinglish harassment
        # (For English text, the neural model decides; rules augment for non-model domains like sextortion and Hinglish)
        is_cyberbullying = 1 if (
            y_pred_model[idx, 1] == 1 or
            cat_scores.get("sextortion", 0.0) >= 50.0 or
            (cat_scores.get("harassment", 0.0) >= 50.0 and any("hinglish" in s.get("signal", "").lower() or "death wish" in s.get("signal", "").lower() for s in signals))
        ) else 0

        # 3. Threat: threat score >= 50 (includes physical threats & Hinglish) OR model threat
        is_threat = 1 if (
            y_pred_model[idx, 2] == 1 or
            cat_scores.get("threat", 0.0) >= 50.0
        ) else 0

        # 4. Toxicity / Offensive Language: model toxicity OR Hinglish abusive language
        is_toxic = 1 if (
            y_pred_model[idx, 3] == 1 or
            (cat_scores.get("abusive_language", 0.0) >= 50.0 and any("hinglish" in s.get("signal", "").lower() for s in signals))
        ) else 0

        # 5. Profanity: model profanity OR profanity heuristic signal
        has_profanity_signal = any(
            any(k in s.get("signal", "").lower() for k in ["profanity", "swear", "vulgar"])
            for s in signals
        )
        is_profanity = 1 if (y_pred_model[idx, 4] == 1 or has_profanity_signal) else 0

        # 6. Clean: no harmful categories active
        is_clean = 1 if (
            is_hate == 0 and
            is_cyberbullying == 0 and
            is_threat == 0 and
            is_toxic == 0 and
            is_profanity == 0
        ) else 0

        y_pred_hybrid.append([is_hate, is_cyberbullying, is_threat, is_toxic, is_profanity, is_clean])

        if (idx + 1) % 2500 == 0 or (idx + 1) == len(texts):
            pct = ((idx + 1) / len(texts)) * 100
            elapsed_h = time.time() - t0_hyb
            print(f"  Hybrid Progress: {idx + 1}/{len(texts)} rows ({pct:.1f}%) evaluated in {elapsed_h:.1f}s", flush=True)

    y_pred_hybrid = np.array(y_pred_hybrid)
    res_hybrid = calculate_metrics(y_true, y_pred_hybrid, LABEL_ORDER)
    print_evaluation_table("EVALUATION (b): FULL HYBRID DETECTION ENGINE (MODEL + RULES + THREAT INTEL)", res_hybrid)

    # ─────────────────────────────────────────────────────────────────────────
    # COMPARISON SUMMARY: Model Alone vs. Hybrid Engine
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 82)
    print("COMPARISON SUMMARY: DISTILBERT ALONE vs. FULL HYBRID ENGINE")
    print("=" * 82)
    print(f"{'Label':<32} {'Model F1':<14} {'Hybrid F1':<14} {'Delta F1':<12}")
    print("-" * 82)

    for i, label in enumerate(LABEL_ORDER):
        m_f1 = res_model_alone["f1s"][i]
        h_f1 = res_hybrid["f1s"][i]
        diff = h_f1 - m_f1
        diff_str = f"{diff:+.4f}" if diff != 0 else "0.0000"
        print(f"{label:<32} {m_f1:<14.4f} {h_f1:<14.4f} {diff_str:<12}")

    print("-" * 82)
    _, _, m_macro_5 = res_model_alone["macro_5"]
    _, _, h_macro_5 = res_hybrid["macro_5"]
    d_macro_5 = h_macro_5 - m_macro_5
    print(f"{'Macro Avg (5 Abuse Labels)':<32} {m_macro_5:<14.4f} {h_macro_5:<14.4f} {d_macro_5:+.4f}")

    _, _, m_macro = res_model_alone["macro"]
    _, _, h_macro = res_hybrid["macro"]
    d_macro = h_macro - m_macro
    print(f"{'Macro Avg (All 6 Labels)':<32} {m_macro:<14.4f} {h_macro:<14.4f} {d_macro:+.4f}")

    _, _, m_micro = res_model_alone["micro"]
    _, _, h_micro = res_hybrid["micro"]
    d_micro = h_micro - m_micro
    print(f"{'Micro Average':<32} {m_micro:<14.4f} {h_micro:<14.4f} {d_micro:+.4f}")
    print("=" * 82)
    print("Evaluation completed successfully.")
    print("=" * 82)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ShieldAI DistilBERT Model and Hybrid Engine on held-out test.csv")
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to held-out test.csv (default: backend/data/test.csv)")
    parser.add_argument("--batch-size", default=64, type=int, help="Batch size for model inference (default: 64)")
    parser.add_argument("--allow-small", action="store_true", help="Allow running on test datasets with fewer than 500 rows")
    args = parser.parse_args()

    evaluate(csv_path=args.csv, batch_size=args.batch_size, allow_small=args.allow_small)
