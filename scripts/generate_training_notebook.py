import json
import os

def create_notebook():
    cells = []
    
    def add_markdown(text):
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" if i < len(text.split('\n')) - 1 else line for i, line in enumerate(text.split('\n'))]
        })
        
    def add_code(text):
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" if i < len(text.split('\n')) - 1 else line for i, line in enumerate(text.split('\n'))]
        })

    # 1. Setup & Installations
    add_markdown("# ShieldAI: Multi-Label Fine-Tuning for Digital Safety\nThis notebook unifies Jigsaw, HateXplain, and OLID datasets to fine-tune `distilbert-base-uncased` as a genuine multi-label classifier for 6 core categories:\n- Hate Speech\n- Cyberbullying / Harassment\n- Threat\n- Toxicity / Offensive Language\n- Profanity\n- Clean")
    
    add_markdown("## Persistent Storage (Google Drive)\nMount Google Drive immediately so that all checkpoints and final models are saved safely even if the runtime disconnects.")
    add_code("""from google.colab import drive
drive.mount('/content/drive')

import os
# Define the base directory for saving model checkpoints and final exports
DRIVE_BASE_DIR = '/content/drive/MyDrive/ShieldAI_MultiLabel'
os.makedirs(DRIVE_BASE_DIR, exist_ok=True)
print(f"All outputs will be saved to: {DRIVE_BASE_DIR}")""")
    
    add_code("!pip install -q transformers datasets evaluate scikit-multilearn scikit-learn torch pandas numpy")
    
    add_code("""import pandas as pd
import numpy as np
import torch
from datasets import load_dataset, Dataset
from sklearn.metrics import classification_report, precision_recall_curve, confusion_matrix
import matplotlib.pyplot as plt
import json
import os

# Set seed for reproducibility
np.random.seed(42)
torch.manual_seed(42)""")

    # 2. Data Sourcing & Unification
    add_markdown("## 1. Data Sourcing & Unification\nMapping strategies:\n\n**Jigsaw:**\n- `toxic` / `severe_toxic` -> Toxicity / Offensive Language\n- `obscene` -> Profanity\n- `threat` -> Threat\n- `insult` -> Cyberbullying / Harassment\n- `identity_hate` -> Hate Speech\n\n**HateXplain:**\n- `hate speech` -> Hate Speech\n- `offensive` -> Toxicity / Offensive Language\n\n**OLID:** (Hierarchical Mapping)\n- `OFF` -> Toxicity / Offensive Language\n- `TIN` -> Cyberbullying / Harassment (Added in addition to OFF)\n- `OFF` + `TIN` + `GRP` -> Hate Speech (Added in addition to OFF and TIN, indicating targeted harassment against a protected class).")
    
    add_code("""# Define taxonomy
LABELS = [
    "Hate Speech", 
    "Cyberbullying / Harassment", 
    "Threat", 
    "Toxicity / Offensive Language", 
    "Profanity", 
    "Clean"
]
num_labels = len(LABELS)

def init_row():
    return {l: 0 for l in LABELS}

unified_data = []

print("Loading Jigsaw...")
import zipfile
import subprocess
from google.colab import userdata

try:
    token = userdata.get('KAGGLE_API_TOKEN')
    if not token:
        raise ValueError("Secret found but empty.")
    os.environ['KAGGLE_API_TOKEN'] = token # Set explicit token as requested
except userdata.SecretNotFoundError:
    raise RuntimeError("KAGGLE_API_TOKEN not found in Colab Secrets. Please add it in the Colab sidebar.")
except Exception as e:
    raise RuntimeError(f"Error accessing KAGGLE_API_TOKEN: {str(e)}")

try:
    print("Downloading Jigsaw dataset from Kaggle...")
    result = subprocess.run(
        ["kaggle", "competitions", "download", "-c", "jigsaw-toxic-comment-classification-challenge"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err = result.stderr.lower() + result.stdout.lower()
        if "unauthorized" in err or "401" in err:
            raise RuntimeError("Kaggle Auth Failed: Invalid or expired KAGGLE_API_TOKEN.")
        elif "forbidden" in err or "403" in err:
            raise RuntimeError("Kaggle Forbidden: You must visit the competition page on Kaggle and accept the rules to download this dataset.")
        else:
            raise RuntimeError(f"Kaggle download failed: {result.stderr}")
            
    with zipfile.ZipFile("jigsaw-toxic-comment-classification-challenge.zip", 'r') as zip_ref:
        zip_ref.extractall("jigsaw_data")
        
    jigsaw_df = pd.read_csv("jigsaw_data/train.csv.zip")
    print(f"Jigsaw dataset loaded successfully! Total rows: {len(jigsaw_df)}")
    print(jigsaw_df.head())
    
except Exception as e:
    raise RuntimeError(f"Failed to load Jigsaw dataset from Kaggle: {str(e)}")

for _, row in jigsaw_df.iterrows():
    new_row = init_row()
    new_row['text'] = row['comment_text']
    
    if row['toxic'] == 1 or row['severe_toxic'] == 1:
        new_row["Toxicity / Offensive Language"] = 1
    if row['obscene'] == 1:
        new_row["Profanity"] = 1
    if row['threat'] == 1:
        new_row["Threat"] = 1
    if row['insult'] == 1:
        new_row["Cyberbullying / Harassment"] = 1
    if row['identity_hate'] == 1:
        new_row["Hate Speech"] = 1
        
    if sum([new_row[k] for k in LABELS if k != "Clean"]) == 0:
        new_row["Clean"] = 1
        
    unified_data.append(new_row)

print("Loading HateXplain...")
try:
    hx = load_dataset("hatexplain", revision="refs/convert/parquet", split="train")
    for row in hx:
        new_row = init_row()
        new_row['text'] = " ".join(row['post_tokens'])
        
        # Majority vote from annotators
        # Parquet format might structure annotators slightly differently (lists vs dicts)
        # Usually it's a dict with 'label' list
        labels = row['annotators']['label'] if isinstance(row['annotators'], dict) else [a['label'] for a in row['annotators']]
        majority_label = max(set(labels), key=labels.count)
        
        if majority_label == 0: # hate speech
            new_row["Hate Speech"] = 1
        elif majority_label == 2: # offensive
            new_row["Toxicity / Offensive Language"] = 1
        elif majority_label == 1: # normal
            new_row["Clean"] = 1
            
        unified_data.append(new_row)
except Exception as e:
    print(f"HateXplain parquet load failed ({e}). Falling back to direct GitHub source...")
    import requests
    response = requests.get("https://raw.githubusercontent.com/hate-alert/HateXplain/master/Data/dataset.json")
    hx_data = response.json()
    for post_id, row in hx_data.items():
        new_row = init_row()
        new_row['text'] = " ".join(row['post_tokens'])
        
        labels = [a['label'] for a in row['annotators']]
        
        # In raw JSON: "hate", "normal", "offensive"
        majority_label = max(set(labels), key=labels.count)
        
        if majority_label == "hate":
            new_row["Hate Speech"] = 1
        elif majority_label == "offensive":
            new_row["Toxicity / Offensive Language"] = 1
        elif majority_label == "normal":
            new_row["Clean"] = 1
            
        unified_data.append(new_row)

print("Loading OLID (OffensEval 2019)...")
olid = load_dataset("tweet_eval", "offensive", split="train", trust_remote_code=True)
# TweetEval offensive only has 0/1 (NOT/OFF). We need the full OLID for hierarchical labels.
# If full OLID isn't on HF easily, we'll simulate the mapping logic here as requested:
try:
    # Attempting to load a full version if available
    olid_full = load_dataset("zapsdcr/olid", split="train", trust_remote_code=True)
    for row in olid_full:
        new_row = init_row()
        new_row['text'] = row['tweet']
        
        is_off = row.get('subtask_a') == 'OFF'
        is_tin = row.get('subtask_b') == 'TIN'
        is_grp = row.get('subtask_c') == 'GRP'
        
        if is_off:
            new_row["Toxicity / Offensive Language"] = 1
        if is_off and is_tin:
            new_row["Cyberbullying / Harassment"] = 1
        if is_off and is_tin and is_grp:
            new_row["Hate Speech"] = 1
            
        if not is_off:
            new_row["Clean"] = 1
            
        unified_data.append(new_row)
except:
    print("Full OLID not immediately available, skipping full hierarchical load in this template. Please provide local CSV.")

df = pd.DataFrame(unified_data)
print(f"Total unified samples: {len(df)}")
df.head()""")

    # 3. Class Balance Sanity Check
    add_markdown("## 2. Class Balance Sanity Check\nWe explicitly verify the counts of positive examples per label. If any label has critically low support (< 500), we halt execution to prevent silent model collapse.")
    add_code("""# Print label counts
label_counts = df[LABELS].sum().to_dict()
print("Positive example counts per label:")
for label, count in label_counts.items():
    print(f"{label}: {count}")

# Sanity check
CRITICAL_THRESHOLD = 500
for label, count in label_counts.items():
    if count < CRITICAL_THRESHOLD:
        raise RuntimeError(f"CRITICAL: The label '{label}' only has {count} examples (below {CRITICAL_THRESHOLD}). " 
                           f"Training will likely collapse on this class. Gather more data before proceeding.")
                           
print("Sanity check passed. Proceeding.")""")

    # 4. Split & Imbalance Handling
    add_markdown("## 3. Iterative Stratified Split & Class Weighting\nBecause labels co-occur, naive random splitting will break the label distributions. We use iterative stratification.")
    add_code("""from skmultilearn.model_selection import iterative_train_test_split

# Prepare features and labels
X = df['text'].values.reshape(-1, 1)
y = df[LABELS].values

# Iterative split: 80% train, 20% temp
X_train, y_train, X_temp, y_temp = iterative_train_test_split(X, y, test_size=0.2)
# Iterative split: temp into 10% val, 10% test
X_val, y_val, X_test, y_test = iterative_train_test_split(X_temp, y_temp, test_size=0.5)

X_train = [x[0] for x in X_train]
X_val = [x[0] for x in X_val]
X_test = [x[0] for x in X_test]

print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")

# Calculate Class Weights using Inverse Document Frequency
# pos_weight = (Total Samples - Positive Samples) / Positive Samples
total_train = len(y_train)
pos_weights = []
for i in range(num_labels):
    pos_count = y_train[:, i].sum()
    neg_count = total_train - pos_count
    weight = neg_count / (pos_count + 1e-5) # Avoid division by zero
    pos_weights.append(weight)

pos_weights_tensor = torch.tensor(pos_weights, dtype=torch.float32)
print("Computed positive weights for BCEWithLogitsLoss:", pos_weights_tensor)""")

    # 5. Tokenization & Dataset Prep
    add_markdown("## 4. Tokenization & Dataset Preparation")
    add_code("""from transformers import AutoTokenizer

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_data(texts, labels):
    encodings = tokenizer(texts, truncation=True, padding=True, max_length=256)
    dataset = Dataset.from_dict({
        'input_ids': encodings['input_ids'],
        'attention_mask': encodings['attention_mask'],
        'labels': labels.astype(np.float32).tolist()
    })
    return dataset

train_dataset = tokenize_data(X_train, y_train)
val_dataset = tokenize_data(X_val, y_val)
test_dataset = tokenize_data(X_test, y_test)""")

    # 6. Model Setup
    add_markdown("## 5. Model Setup & Custom Loss Trainer")
    add_code("""from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, EarlyStoppingCallback
from torch.nn import BCEWithLogitsLoss

model = AutoModelForSequenceClassification.from_pretrained(
    model_name, 
    num_labels=num_labels,
    problem_type="multi_label_classification"
)

# Custom Trainer to inject pos_weight
class MultiLabelTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        
        loss_fct = BCEWithLogitsLoss(pos_weight=pos_weights_tensor.to(model.device))
        loss = loss_fct(logits, labels)
        
        return (loss, outputs) if return_outputs else loss

from sklearn.metrics import f1_score
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    # Sigmoid to get probabilities
    probs = 1 / (1 + np.exp(-logits))
    # Temporary 0.5 threshold for early stopping monitoring
    preds = (probs > 0.5).astype(int)
    macro_f1 = f1_score(labels, preds, average='macro', zero_division=0)
    return {"macro_f1": macro_f1}

training_args = TrainingArguments(
    output_dir=f"{DRIVE_BASE_DIR}/checkpoints",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="macro_f1",
    fp16=True, # Mixed precision
    dataloader_num_workers=2
)

trainer = MultiLabelTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)""")

    # 7. Training
    add_markdown("## 6. Execution")
    add_code("""# RUN TRAINING
trainer.train()""")

    # 8. Calibration
    add_markdown("## 7. Calibration & Threshold Tuning\nTune threshold per label using Precision-Recall curves to maximize F1-score.")
    add_code("""print("Running inference on validation set for calibration...")
val_preds = trainer.predict(val_dataset)
val_logits = val_preds.predictions
val_labels = val_preds.label_ids
val_probs = 1 / (1 + np.exp(-val_logits)) # Sigmoid

optimal_thresholds = []

for i in range(num_labels):
    precision, recall, thresholds = precision_recall_curve(val_labels[:, i], val_probs[:, i])
    # Compute F1 for each threshold
    f1_scores = np.divide(2 * precision * recall, (precision + recall), out=np.zeros_like(precision), where=(precision + recall) != 0)
    best_idx = np.argmax(f1_scores)
    
    # thresholds array has len(precision)-1
    best_thresh = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    optimal_thresholds.append(float(best_thresh))
    
    print(f"{LABELS[i]}: Best Threshold = {best_thresh:.4f} (Val F1 = {f1_scores[best_idx]:.4f})")

# Construct threshold mapping for export
threshold_mapping = {LABELS[i]: optimal_thresholds[i] for i in range(num_labels)}""")

    # 9. Evaluation
    add_markdown("## 8. Final Evaluation on Test Set")
    add_code("""print("Evaluating on holdout test set...")
test_preds = trainer.predict(test_dataset)
test_probs = 1 / (1 + np.exp(-test_preds.predictions))

# Apply calibrated thresholds
test_pred_labels = np.zeros_like(test_probs)
for i in range(num_labels):
    test_pred_labels[:, i] = (test_probs[:, i] >= optimal_thresholds[i]).astype(int)

print(classification_report(test_y_true := test_preds.label_ids, test_pred_labels, target_names=LABELS, zero_division=0))

# Confusion Matrices
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()
for i in range(num_labels):
    cm = confusion_matrix(test_y_true[:, i], test_pred_labels[:, i])
    axes[i].imshow(cm, cmap='Blues')
    axes[i].set_title(LABELS[i])
    axes[i].set_xticks([0,1])
    axes[i].set_yticks([0,1])
    axes[i].set_xlabel('Predicted')
    axes[i].set_ylabel('True')
    # Add text
    for x in range(2):
        for y in range(2):
            axes[i].text(y, x, str(cm[x,y]), ha='center', va='center', color='red' if cm[x,y]>cm.max()/2 else 'black')
plt.tight_layout()
plt.show()""")

    # 10. Export
    add_markdown("## 9. Export for Antigravity")
    add_code("""export_path = f"{DRIVE_BASE_DIR}/final_model"
os.makedirs(export_path, exist_ok=True)

# Save Model & Tokenizer
model.save_pretrained(export_path)
tokenizer.save_pretrained(export_path)

# Save Thresholds
with open(os.path.join(export_path, "thresholds.json"), "w") as f:
    json.dump(threshold_mapping, f, indent=4)

print(f"Model, tokenizer, and thresholds.json saved to {export_path}")
print("Ready to push to HuggingFace Hub or upload to Drive.")
# Uncomment to push to hub:
# model.push_to_hub("your-username/shieldai-distilbert-multilabel", private=True)
# tokenizer.push_to_hub("your-username/shieldai-distilbert-multilabel", private=True)""")

    # 11. Probe Test
    add_markdown("## 10. Probe Test (Self-Verify)")
    add_code("""probe_text = "You're worthless, just disappear from here you fucker asshole"
print(f"Testing probe: '{probe_text}'")

inputs = tokenizer(probe_text, return_tensors="pt", truncation=True, max_length=256).to(model.device)
with torch.no_grad():
    logits = model(**inputs).logits
    probs = torch.sigmoid(logits).squeeze().cpu().numpy()

print("\\nPredictions:")
for i, label in enumerate(LABELS):
    is_triggered = probs[i] >= optimal_thresholds[i]
    print(f"[{'X' if is_triggered else ' '}] {label}: {probs[i]*100:.1f}% (Threshold: {optimal_thresholds[i]*100:.1f}%)")""")

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notebooks"), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notebooks", "ShieldAI_MultiLabel_FineTuning.ipynb"), "w") as f:
        json.dump(notebook, f, indent=2)
        
    print("Notebook generated at ../notebooks/ShieldAI_MultiLabel_FineTuning.ipynb")

if __name__ == "__main__":
    create_notebook()
