# Online Harassment Detection System

ML-based web app that classifies text as harassing or non-harassing, with
a category breakdown (hate speech / offensive language / none) and an admin
dashboard for reviewing flagged content.

**Current status:** baseline model (TF-IDF + Logistic Regression) trained
and working end-to-end, full stack tested (Flask + React + dashboard).
DistilBERT and audio/video transcription are built and wired in, but need
one thing this dev environment can't do: download model weights from the
open internet. See "What's tested vs. what needs your machine" below.
See `docs/sprint_plan.md` for the week-by-week plan.

## Quick start (local dev, no Docker)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ml/train_baseline.py     # trains and saves the model (~10 sec)
python app.py                   # starts Flask on http://localhost:5000
```

### 2. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev                     # starts Vite on http://localhost:5173
```

Open http://localhost:5173 — the analyzer form and dashboard both talk to
the Flask backend via the `/api` proxy configured in `vite.config.js`.

## Quick start (Docker)

```bash
docker compose up --build
```

Backend: http://localhost:5000, Frontend: http://localhost:3000

Note: you must run `python ml/train_baseline.py` locally at least once
before building the Docker image, so `backend/models/*.joblib` exists
(it's mounted as a volume, not baked into the image).

## Project structure

```
backend/
  app.py                    Flask API — predict, predict/audio, health, admin stats/recent
  ml/
    preprocess.py            Text cleaning, shared by baseline training + inference
    train_baseline.py        TF-IDF + Logistic Regression training script
    predict.py                Loads baseline model, classifies text
    train_transformer.py      DistilBERT fine-tuning (local/GPU-machine version)
    predict_transformer.py    Loads DistilBERT model, classifies text
    transcribe.py              Whisper transcription -> classifier pipeline
  models/                    Saved model artifacts (gitignored, regenerate locally)
    distilbert/               DistilBERT goes here after training (see below)
frontend/
  src/
    App.jsx
    components/
      AnalyzeForm.jsx         User-facing text analysis form
      Dashboard.jsx            Admin stats + chart + recent flagged messages
data/
  raw/                        Source dataset + notes on label mapping
notebooks/
  01_eda.ipynb                Sprint 1 exploratory data analysis
  02_train_distilbert.ipynb   Colab notebook — run this to actually train DistilBERT
docs/
  sprint_plan.md              Week-by-week plan for the 2-4 week timeline
```

## Training DistilBERT (needs Colab, not this repo alone)

1. Upload `notebooks/02_train_distilbert.ipynb` to https://colab.research.google.com
2. Runtime → Change runtime type → T4 GPU
3. Run all cells. It downloads the same dataset, trains, prints a classification
   report you can directly compare against the baseline's, then downloads a
   `distilbert_model.zip`
4. Unzip it into `backend/models/distilbert/` on your machine
5. Restart `python app.py` — it auto-detects the model and routes `/predict`
   to DistilBERT instead of the baseline, no code changes needed

## What's tested vs. what needs your machine

Everything below was actually run and verified, not just written:
- Dataset load, preprocessing, baseline training (86% accuracy)
- Flask API — all endpoints, including error handling on bad input
- React frontend — builds clean, connects to the API
- `/predict/audio` — file validation and error handling (confirmed it fails
  cleanly on missing/wrong-type files, and reaches the transcription step
  correctly on a valid file)

What's written and syntax-checked, but needs you to run it once with real
internet access (Hugging Face and Whisper's model host are both blocked in
the sandbox that built this repo):
- `train_transformer.py` / `02_train_distilbert.ipynb` — standard HuggingFace
  Trainer API, but not test-run end-to-end here
- `transcribe.py` — Whisper's package installs and imports fine; the actual
  model weight download (~150MB, one-time) needs to happen on your machine

Run these yourself the first time rather than assuming they're bug-free the
way `train_baseline.py` is — that one was actually executed and verified.

## Known placeholder

`LOG_STORE` in `app.py` is in-memory, not MongoDB — flagged messages reset
when the server restarts. Swap this out in Sprint 3 (see `docs/sprint_plan.md`).

## Known limitations (be upfront about these in your report)

1. English only — no multilingual support yet
2. Class imbalance — hate_speech is 5.8% of the training data, so precision
   on that specific category is currently weak (~32%). See `data/raw/README.md`.
3. Implicit/coded threats without profanity are hard for the baseline model
   to catch — e.g. "I know where you live" scored as non-harassing in testing.
   This is the main argument for the DistilBERT upgrade in week 2.
4. No explainability (SHAP/LIME) yet — flagged messages don't come with a
   "why" beyond the confidence score.

See `docs/sprint_plan.md` for the full timeline and what's explicitly
out of scope for this deadline.
