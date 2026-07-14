# Sprint Plan — 3 Week Build (Trimmed Advanced Scope)

Scoped for a 2-4 week client deadline. This is the trimmed "advanced" build:
DistilBERT + Flask + React + MongoDB + Docker, deployed on Render.

Cut from the full synopsis and pushed to "future scope" in the report:
multilingual support, SHAP/LIME explainability, browser extension,
dual-database (MySQL + MongoDB) architecture.

---

## Week 1 — Data + Baseline (Sprint 1 & first half of Sprint 2)

- [x] Project scaffold, environment setup — **done**
- [x] Dataset acquired (Davidson et al., 24,783 labeled tweets) — **done**
- [x] Preprocessing pipeline — **done** (`backend/ml/preprocess.py`)
- [x] Baseline model: TF-IDF + Logistic Regression — **done** (86% accuracy,
      but weak on hate_speech precision — expected, document this)
- [ ] Run the EDA notebook (`notebooks/01_eda.ipynb`), save 2-3 charts for
      your report (class balance, tweet length, top words per class)
- [ ] Try a second classical model (Linear SVM) for comparison in your report

**Deliverable by end of week 1:** working baseline classifier + EDA writeup.

## Week 2 — DistilBERT + API + Frontend (Sprint 2 & Sprint 3)

- [x] `train_transformer.py` and `02_train_distilbert.ipynb` written —
      **but not yet actually run.** Run the Colab notebook yourself: Runtime →
      T4 GPU → Run all. This is the one remaining "did it actually work" check.
- [ ] Once trained, compare DistilBERT vs. baseline on the same test set —
      precision/recall/F1 per class, not just accuracy (this comparison IS
      your "evaluate multiple algorithms" objective from the synopsis — you
      don't need LSTM AND BERT, picking two and comparing them well is
      stronger than four done shallowly)
- [x] Flask REST API (`/predict`, `/predict/audio`, `/admin/stats`, `/admin/recent`)
      — **done and tested**, auto-routes to DistilBERT once you drop the
      trained model into `backend/models/distilbert/`
- [x] React frontend: analyze form + admin dashboard — **done and tested**
- [ ] Swap in-memory `LOG_STORE` in `app.py` for real MongoDB storage
- [x] Audio/video transcription (`transcribe.py`, Whisper) — **added as a
      scoped stretch feature.** Package installs and the API endpoint is
      tested; the model weight download needs to happen on your machine
      once (blocked in the dev sandbox that built this).

**Deliverable by end of week 2:** full working app, classical model in prod,
DistilBERT trained and benchmarked (run the notebook yourself and confirm),
audio transcription working locally.

### On "video-based harassment detection"

Scoped deliberately as transcription + text classification (Whisper → your
existing model), NOT frame-by-frame visual behavior analysis. The latter is
a genuinely different, harder computer vision problem with no clean public
dataset to train on ethically — treat it as out of scope, not as something
to attempt in the time remaining. State this scope decision explicitly in
your report; it reads as good judgment, not a missing feature.

## Week 3 — Deploy + Polish + Document

- [x] Docker + docker-compose — **done**
- [ ] Deploy backend + frontend to Render (or your platform of choice)
- [ ] Basic error handling / input validation pass (empty text, oversized
      input, non-English input behaving predictably rather than crashing)
- [ ] Write up known limitations in your report (class imbalance, coded/
      implicit threats being harder to catch, English-only, no explainability
      yet) — this is expected and strengthens the report, not a weakness to hide
- [ ] Record a short demo (screen recording) as a deliverable alongside the
      live link, in case deployment has hiccups on demo day

**Deliverable by end of week 3:** deployed, working, documented.

---

## If you get a 4th week

Pick ONE stretch item, not several:
- SHAP explainability on the baseline model only (much faster to set up than
  on DistilBERT)
- Basic Hindi support using a second, smaller multilingual dataset
- MySQL alongside MongoDB if the client specifically asked for both

## Explicitly out of scope for this timeline

State these plainly in your report as "Future Scope" (your synopsis already
has a section for this — reuse it):
- Multilingual detection (Hindi, Kannada, Tamil)
- Live social media API integration
- Browser extension
- Full XAI module across all models
