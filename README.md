# ShieldAI — Online Harassment Detection System

An ML-based web application that classifies text, audio/video, and screenshots as harassing or non-harassing, complete with category breakdowns (hate speech / offensive language / clean), advanced risk scoring, semantic duplicate detection, and an AI-powered admin dashboard for reviewing flagged content.

## Key Features

- **Multi-modal Analysis**: Analyzes raw text, audio/video files (via Whisper transcription), and images/screenshots (via EasyOCR).
- **Dual ML Models**: Supports both a fast TF-IDF + Logistic Regression baseline and an advanced DistilBERT transformer model.
- **Explainability**: Word-level contribution highlighting (TF-IDF × LR coefficients) to explain *why* the baseline model flagged content.
- **Risk Scoring & Incident Summarization**: Automatically scores the risk severity of flagged items and generates readable incident summaries using Groq.
- **Semantic Clustering**: Detects repeated/similar harassment campaigns using MiniLM embeddings.
- **Secure Admin Dashboard**: JWT-authenticated React dashboard to view trends, anomalies, and recently flagged items.

---

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
*Note: Make sure MongoDB is running locally on port 27017 or configure the `MONGO_URI` in your `.env` file.*

### 2. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev                     # starts Vite on http://localhost:5173
```

Open http://localhost:5173 — the analyzer forms and dashboard both talk to the Flask backend via the `/api` proxy configured in `vite.config.js`.

---

## Quick start (Docker)

```bash
docker compose up --build
```

- Backend: http://localhost:5000
- Frontend: http://localhost:3000

*Note: you must run `python ml/train_baseline.py` locally at least once before building the Docker image, so `backend/models/*.joblib` exists (it's mounted as a volume, not baked into the image).*

---

## Project Structure

```
backend/
  app.py                    Flask application factory & middleware setup
  api/                      Modular Flask Blueprints
    routes_public.py        Public analysis endpoints (/predict, /predict/audio, etc.)
    routes_admin.py         JWT-protected admin endpoints (/admin/stats, /admin/login)
  services/                 Business Logic Layer
    auth_service.py         JWT issuance and validation
    db_service.py           MongoDB persistence and anomaly detection
    llm_service.py          Groq-based incident summarization
    model_service.py        ML inference orchestration
    risk_service.py         Risk scoring engine
    similarity_service.py   MiniLM-based semantic clustering
  ml/                       Core ML Pipelines
    preprocess.py           Text cleaning logic
    train_baseline.py       TF-IDF + LR training script
    predict.py              Baseline inference
    train_transformer.py    DistilBERT training script
    predict_transformer.py  DistilBERT inference
    transcribe.py           Whisper transcription
    ocr.py                  EasyOCR text extraction
  models/                   Saved model artifacts (gitignored)

frontend/
  src/
    App.jsx                 Main router & Layout
    api/client.js           Centralized API fetch client with JWT injection
    hooks/                  Reusable custom React hooks (useAuth, usePredict, useAdminData)
    components/
      common/               Shared UI elements (Card, Button, FileUpload, LoadingState)
      dashboard/            Admin Dashboard subcomponents (Charts, Stats, Table)
      prediction/           Analysis result subcomponents (RiskBadge, ConfidenceBar, Summary)
      auth/                 LoginForm component
      AnalyzeForm.jsx       Text & Audio upload form
      ScreenshotAnalyzeForm Image upload form
      ResultDisplay.jsx     Orchestrates prediction visualization
```

---

## Training DistilBERT

1. Upload `notebooks/02_train_distilbert.ipynb` to https://colab.research.google.com
2. Runtime → Change runtime type → T4 GPU
3. Run all cells to train and download a `distilbert_model.zip`
4. Unzip it into `backend/models/distilbert/`
5. Restart `python app.py` — it auto-detects the model and routes `/predict` to DistilBERT instead of the baseline.

---

## Recent Architecture Improvements

This project recently underwent a comprehensive 5-phase refactoring to achieve enterprise-grade maintainability:

1. **Backend Structural Overhaul**: Segregated business logic into a `services/` layer and isolated core ML pipelines.
2. **Feature Extensions**: Added Groq LLM summarization, semantic clustering, risk scoring, and MongoDB persistence.
3. **API Modularization**: Split the monolithic `app.py` into distinct `routes_public.py` and `routes_admin.py` blueprints, adding robust JWT authentication middleware.
4. **Frontend Infrastructure**: Introduced a centralized `apiClient` and reusable custom hooks for state management.
5. **Frontend Component Breakdown**: Dismantled large monolithic React components into atomic, single-responsibility components with strict `prop-types` validation.

---

## Known Limitations

1. **English only** — no multilingual support yet.
2. **Class imbalance** — `hate_speech` is a minority class in the training data, so precision on that specific category is currently weak in the baseline model.
3. **Implicit Threats** — coded threats without profanity are hard for the baseline model to catch. This is mitigated by the DistilBERT model.
