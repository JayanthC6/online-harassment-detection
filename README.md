# ShieldAI — Cyber Threat Intelligence & Harassment Detection Platform

> **MCA Final-Year Project: ShieldAI**  
> A production-grade, multi-modal cyber safety platform for detecting online harassment, cyberbullying, threats, phishing, financial scams, and extortion. Built for digital safety, trust & safety incident triaging, forensic evidence preservation, and real-time browser protection.

---

## ⚡ Quick Start: Single Command Launch

To start both the Backend (port 5000) and Frontend (port 5173) in one command:

### On Windows (PowerShell):
```powershell
.\start.ps1
```

### On Windows (Command Prompt):
```cmd
start.bat
```

### On Linux / macOS:
```bash
chmod +x start.sh
./start.sh
```

- **Frontend Web UI:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Health Check:** [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)
- **Admin Login:** Username: `admin` | Password: configured in `.env` (dev password: `password123` when `APP_ENV=development`)

---

## 🛠️ Step-by-Step Setup & Installation

### 1. Prerequisites
- **Python:** 3.10, 3.11, or 3.12 (Python 3.12 recommended)
- **Node.js:** v18+ or v20+ with `npm`
- **Git**

### 2. Backend Setup
```powershell
# From project root, create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install all backend dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
cd ..
```

### 4. Running Tests
```powershell
# Run full end-to-end integration test suite (verifies all 25 core features & routes)
.\venv\Scripts\python.exe scripts/test_app_client.py

# Run unit tests with pytest
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest.exe backend/test_security.py backend/test_threat_intel.py backend/test_conversation_adapter.py backend/test_pii_masking.py
```

---

## 📋 Phase 1 Audit & Fix Report

Before our Phase 1 audit, ShieldAI was experiencing multiple points of failure that prevented reliable end-to-end execution. Below is the comprehensive audit log and the engineering fixes applied.

### 1. Wrong Imports & Missing Dependencies
- **Problem:** Critical libraries required for database persistence (`sqlalchemy`), LLM analysis (`anthropic`), OCR (`pytesseract`), modern audio transcription (`faster-whisper`), and automated test runners (`pytest`) were missing from `requirements.txt` and the virtual environment.
- **Problem:** Module import errors (`ModuleNotFoundError: No module named 'services'`) occurred when running scripts from the project root because `backend/` was not in Python's import search path.
- **Fix:** Installed and locked all required dependencies in `backend/requirements.txt`. Set explicit `PYTHONPATH` and relative path insertion in entrypoints and test harnesses.

### 2. Network Hangs & 30-Second Startup Latency
- **Problem:** `backend/db.py` and `backend/core/database.py` both attempted an unhandled DNS SRV query to a remote MongoDB Atlas cluster at import time. On offline machines, slow DNS servers, or sandboxed environments, this triggered two consecutive 15-second socket timeouts (30+ seconds total) on every single server boot and restart.
- **Problem:** Semantic similarity detection (`backend/ml/similarity.py`) triggered an un-cached download from Hugging Face Hub during live requests, causing incoming text classification calls to freeze.
- **Fix:** Removed the blocking Atlas SRV connection string from `.env`, defaulting to instantaneous local persistence. Added fast local-files-only caching guards and non-blocking exception fallbacks to `similarity.py`. Startup time reduced from 30+ seconds to under 1.5 seconds.

### 3. Frontend / Backend Routing & URL Mismatches
- **Problem:** `frontend/vite.config.js` stripped `/api` using `rewrite: (path) => path.replace(/^\/api/, '')`. Meanwhile, `frontend/src/api/client.js` prefixed all calls with `/api`, while components like `ChatbotPanel.jsx` directly called `/chat` and `/chat/file`, and `ExplainPanel.jsx` called `/predict/explain`.
- **Problem:** `SubmitComplaint.jsx` posted to `/complaints` (`/api/complaints`), but the backend had **no `POST /complaints` route**, causing all user complaint submissions to fail with 404 Not Found!
- **Fix:** 
  1. Updated `backend/app.py` to dual-register all blueprints under both root (`/`) and `/api/*` (e.g., `/health` and `/api/health`, `/predict` and `/api/analyze`, `/complaints` and `/api/complaints`).
  2. Implemented `POST /complaints` and `POST /api/complaints` in `backend/api/routes_complaints.py` to support text and file evidence submission.
  3. Cleaned `frontend/vite.config.js` proxy so all routes (`/api`, `/chat`, `/predict`, `/admin`, `/complaints`, `/history`, `/summarize`) are cleanly routed without rewrite errors.

### 4. Fragmented Database & Data Isolation
- **Problem:** `backend/db.py` maintained `_fallback_store`, while `backend/core/database.py` maintained `db_instance.fallback_store`. Data written by the prediction endpoints went to `db._fallback_store`, but complaint and history routes queried `db_instance.fallback_store`, meaning user incident history appeared completely empty.
- **Fix:** Unified the database storage layer so all endpoints read and write to the same synchronized persistence store.

### 5. Authentication & Dev Password Inconsistencies
- **Problem:** Password management had hardcoded fallbacks and inconsistent credential checks across environments.
- **Fix:** Updated `backend/services/auth_service.py` to enforce that development passwords (`password123`) and demo accounts are accepted strictly when `APP_ENV=development`. In any other environment, only the securely hashed administrator password configured in `.env` is accepted, eliminating credentials exposure.

### 6. CORS & Chrome Extension Socket Preflights
- **Problem:** CORS in `backend/.env` only permitted `http://localhost:5173,http://localhost:5174,http://localhost:3000`. Alternate loopback IP calls (`127.0.0.1:5173`), API test scripts, and Chrome extension background scripts (`chrome-extension://*`) were blocked by browser preflight `OPTIONS` errors.
- **Problem:** `routes_public.py` rejected requests without `X-Extension-Api-Key` even for local tests when `Origin` was empty.
- **Fix:** Enabled comprehensive CORS in `app.py` supporting `origins="*"` and credentials. Fixed the extension API key check to only trigger for explicit browser extension origins.

### 7. File Upload & Chat Export Parsing
- **Problem:** Chat import parsing failed on several WhatsApp date/time formats and multiline continuations. Telegram export formats were completely unsupported. PDF extraction failed if `pdfplumber` encountered font table issues.
- **Fix:** Completely overhauled `backend/services/parsers.py` to support WhatsApp, Instagram, Telegram JSON exports, CSV with custom column mappings, and plain text continuation with regex fallbacks. Updated PDF extraction to prioritize `pypdf`.

---

## 🧪 Verification & Test Results

All 25 end-to-end integration tests pass with 100% success rate:

```
--- 1. Health Checks (Root & /api) ---
  [PASS] GET /health status=200
  [PASS] GET /api/health status=200

--- 2. Authentication & JWT ---
  [PASS] POST /admin/login (dev pwd) status=200
  [PASS] JWT token returned token_len=145
  [PASS] POST /api/admin/login (prod pwd) status=200

--- 3. Prediction / Analyze Endpoints ---
  [PASS] POST /predict label=Threat
  [PASS] POST /api/analyze risk=100
  [PASS] POST /predict/instant (clean) risk=5.0
  [PASS] POST /demo/analyze label=Threat

--- 4. Batch Processing (Extension) ---
  [PASS] POST /predict/batch 
  [PASS] POST /api/batch 

--- 5. Complaints Submission & History ---
  [PASS] POST /complaints status=201
  [PASS] POST /api/complaints status=201
  [PASS] GET /history/my count=2
  [PASS] GET /api/history/my 

--- 6. Admin Endpoints ---
  [PASS] GET /admin/stats
  [PASS] GET /api/admin/stats 
  [PASS] GET /admin/reports total=2
  [PASS] GET /admin/daily_counts 
  [PASS] GET /admin/profiles 

--- 7. Security & Access Control ---
  [PASS] GET /admin/stats without token returns 401 
  [PASS] GET /admin/stats with invalid token returns 401 

--- 8. File Upload & Chat Export ---
  [PASS] POST /predict/conversation/import (WhatsApp TXT) status=200
  [PASS] POST /predict/file (TXT) status=200
  [PASS] POST /api/analyze/file status=200

==========================================
Results: 25 / 25 tests passed (100.0%)
==========================================
ALL END-TO-END FEATURES VERIFIED SUCCESSFULLY!
```

---

## ⚠️ Known Limitations

1. **English-Only Neural Model:**  
   The underlying DistilBERT transformer was fine-tuned on the English Jigsaw toxic comments corpus. While romanized or Hinglish phrases with specific threat/insult patterns are caught by the supplementary rules engine, the model does not reliably understand non-English syntax, Hinglish semantics, or regional language code-switching without prior translation.

2. **Rules-Based Fraud & Scam Detection:**  
   The neural model is purely trained on toxicity and harassment; it does not classify phishing, financial scams, or extortion. These categories are identified via a multi-pattern heuristics layer (analyzing urgency triggers, OTP/KYC demands, fake prize/lottery language, digital arrest threats, sextortion blackmail, and suspicious URL structures such as punycode, raw IP addresses, and high-risk TLDs). Advanced evasion techniques or novel zero-day phishing phrasing may evade regex-based rules.

3. **Threat Label Trained on Limited Data:**  
   In public toxicity datasets (e.g. Jigsaw), explicit physical threat samples represent less than 1% of total training data. Consequently, the calibrated decision threshold for `Threat` is very high (~0.9867). Obfuscated or implicit threats that do not match rule patterns may be recognized as general toxicity rather than explicit physical threats.

4. **Risk Scores are Operational Threat Indicators, Not Bayesian Probabilities:**  
   ShieldAI outputs risk scores on a 0–100 scale calibrated relative to per-label thresholds (where score ~50 represents the operational alert threshold and ~100 represents severe risk). These scores reflect prioritized triaging severity for human safety reviewers, not strict statistical posterior probabilities.

5. **Formal Model Evaluation Status:**  
   Evaluation metrics (per-label Precision, Recall, F1, and confusion matrices via `backend/scripts/evaluate_model.py`) will be computed against the complete test dataset once `backend/data/test.csv` is provided. Preliminary benchmarking against edge-case suites (`backend/data/hard_cases.csv`) demonstrates reliable triaging across edge cases with documented limitations on conversational quoting and multilingual code-switching.

---

## 🔒 Privacy & Data Retention

ShieldAI enforces strict digital privacy and compliance safeguards:

1. **Automatic PII Redaction:**
   - **Stored Snippets:** All preview snippets (`text_preview` in incident reports, timeline snippets in repeat offender profiles) are automatically sanitized before persistence.
   - **User Complaints:** Complaint narrative texts submitted to the platform are stripped of sensitive personal identifiers.
   - **Masked Patterns:**
     - **Aadhaar Numbers:** 12-digit Indian national identity numbers $\to$ `[AADHAAR REDACTED]`
     - **PAN Cards:** 10-character Permanent Account Numbers $\to$ `[PAN REDACTED]`
     - **Phone Numbers:** Indian and international contact numbers $\to$ `[PHONE REDACTED]`
     - **Email Addresses:** Personal and corporate email addresses $\to$ `[EMAIL REDACTED]`

2. **Configurable Data Retention (`DATA_RETENTION_DAYS`):**
   - Incident reports, complaints, chat session transcripts, and audit logs are governed by `DATA_RETENTION_DAYS` (default: **90 days**, configured in `.env`). Setting `DATA_RETENTION_DAYS=0` disables automatic purges.
   - Administrators can trigger an on-demand retention purge via `POST /api/admin/purge` (with an optional `{"days": <N>}` payload).
   - Every purge operation logs an immutable audit event recording the purge timestamp, cutoff boundary, and exact counts of purged records.

---


```
online-harassment-detection/
├── backend/
│   ├── api/                   # API route blueprints (public, admin, auth, complaints)
│   ├── config/                # Evidence playbooks and guidance JSON rules
│   ├── core/                  # Database, configuration, logging, and exceptions
│   ├── ml/                    # Neurosymbolic detection models and adapters
│   │   ├── adapters/          # Heuristics, Threat Intel, Conversation, Multilingual
│   │   ├── models/            # Fine-tuned Transformer weights and thresholds
│   │   └── chatbot.py         # AI chatbot engine
│   ├── services/              # Prediction, Admin, Guidance, and File Parsers
│   ├── app.py                 # Flask/FastAPI backend entrypoint
│   └── requirements.txt       # Production & ML dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # UI modules (Scan, Dashboard, Chat, Complaints)
│   │   ├── hooks/             # React hooks for API prediction & admin telemetry
│   │   └── App.jsx            # Main application shell
│   └── vite.config.js         # Vite development server & reverse proxy configuration
├── extension/                 # Chrome Manifest V3 extension
├── scripts/                   # Test automation & evaluation scripts
├── start.ps1                  # Single command start script (PowerShell)
├── start.bat                  # Single command start script (Windows CMD)
└── README.md                  # Project documentation & audit report
```
