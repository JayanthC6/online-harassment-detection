# ShieldAI — Cyber Threat Intelligence & Harassment Detection Platform

> **A production-grade, multi-modal cyber safety platform** for detecting online harassment, phishing, scams, threats, and social engineering attacks. Built for trust & safety teams, digital forensic investigators, and end-users reporting cyber incidents.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Setup & Installation](#setup--installation)
7. [Environment Variables](#environment-variables)
8. [API Reference](#api-reference)
9. [Role-Based Access Control](#role-based-access-control)
10. [Security & Privacy](#security--privacy)
11. [Running Tests](#running-tests)
12. [Docker Deployment](#docker-deployment)
13. [Chrome Extension](#chrome-extension)

---

## Overview

ShieldAI is a full-stack forensic trust & safety platform that combines a **fine-tuned DistilBERT transformer**, a **multi-label heuristic engine**, and **external threat intelligence feeds** to classify, score, and explain digital abuse incidents.

The platform serves two primary audiences:

| Persona | Interface | Purpose |
|---|---|---|
| **End User / Victim** | Threat Hunt console | Analyze individual messages, conversations, screenshots, or audio files for threats |
| **Admin / Moderator** | Cyber SOC Dashboard | Review incident queues, manage behavioral profiles, analyze trends |

---

## Core Features

### 1. Neurosymbolic Intelligence Pipeline

ShieldAI uses a **dual-engine fusion** architecture to maximize both recall and explainability:

- **Neural Engine** — Fine-tuned `distilbert-base-uncased` transformer model for deep contextual classification. Falls back gracefully to a scikit-learn baseline (TF-IDF + Logistic Regression) if the model weights are unavailable.
- **Heuristic Multi-Label Engine** — A deterministic ruleset (`heuristic.py`) layered on top of the primary model to detect additional threat categories the neural model may underweight (e.g., extortion, blackmail, impersonation, investment fraud).
- **Noisy-OR Fusion** — Risk scores from neural and heuristic signals are fused using Noisy-OR logic, ensuring any strong signal from either engine correctly escalates the final risk score.
- **Risk Score Computation** — A composite `risk_score` (0–100) is derived from the primary category's base severity, confidence weighting, secondary label contributions (20% weight each), and a multi-vector attack bonus.
- **Transformer Explainability** — Token-level attribution via `Captum` (Integrated Gradients) highlights exactly which words drove a neural classification, displayed in the `Token Heatmap` UI component.

**Detected categories include:**
`Threat`, `Extortion`, `Blackmail`, `Self Harm`, `Hate Speech`, `Cyberbullying / Harassment`, `Sexual Harassment`, `Identity Attack`, `Phishing`, `Scam`, `Fraud`, `Impersonation`, `Social Engineering`, `Spam`, `Profanity`, `Toxicity / Offensive Language`, `Clean`

---

### 2. External Threat Intelligence

Integrated OSINT and threat intel feeds run asynchronously alongside every text analysis:

| Check | Implementation | Trigger |
|---|---|---|
| **Google Safe Browsing** | REST API v4 lookup | URLs extracted from message text |
| **Typosquatting Detection** | Levenshtein distance against brand list | Domains near `paypal.com`, `apple.com`, `microsoft.com`, etc. |
| **Domain Age (WHOIS)** | `python-whois` with async timeout | Domains < 30 days old flagged as phishing indicators |
| **HIBP Breach Check** | Have I Been Pwned API | Email addresses extracted via PII detector |
| **Social Engineering Patterns** | Regex ruleset (17 pattern classes) | Credential requests, OTP pressure, ransom demands, gift card fraud |
| **URL Shortener Detection** | Domain allowlist check | `bit.ly`, `tinyurl.com`, `t.co`, etc. |
| **Dangerous Scheme Detection** | Regex | `javascript:` and `data:` URI injection attempts |
| **IP-Based URL Detection** | Regex + socket | URLs using raw IP addresses instead of domains |

All external calls use a **10-minute TTL cache** (`cachetools`) and strict async timeouts to prevent pipeline blocking.

---

### 3. Multi-Modal Input Support

The Threat Hunt console accepts multiple input modalities via a single unified analysis endpoint:

| Modality | Technology | Notes |
|---|---|---|
| **Plain text** | Direct classifier input | Single message or multi-paragraph |
| **Conversation files** | `parsers.py` | Parses exported WhatsApp `.txt` and Instagram `.json` chat logs |
| **Screenshots / Images** | `EasyOCR` + `OpenCV` | Extracts text from image screenshots for classification |
| **Audio / Video** | `OpenAI Whisper` (base model) | Transcribes speech to text, then classifies transcript |
| **Documents** | Groq LLM extraction | PDFs, `.docx`, `.txt`, `.log`, `.csv` parsed for chat-like content |

---

### 4. PII Masking & Evidence Handling

- **PII Extraction** — Detects and extracts emails, phone numbers, names (using regex + heuristics) from submitted content.
- **PII Masking** — All content returned via the public API is automatically sanitized through `mask_pii()` before reaching the frontend. Raw PII is never exposed in API responses.
- **Evidence Playbooks** — Category-specific evidence collection plans (`config/evidence_playbooks.json`) are generated alongside each prediction, providing step-by-step forensic guidance for preserving evidence, contacting platforms, and escalating to law enforcement.
- **Personalized Safety Plans** — Victim-facing guidance generated per incident type, displayed in the UI as structured action cards.

---

### 5. Behavioral Intelligence & Actor Profiling

A persistent actor profiling engine tracks repeat offenders across incidents:

- **Incremental Profiling** — Every flagged message logged through the admin pipeline updates the actor's behavioral profile in MongoDB.
- **Behavior Score** — A computed aggregate score (0–100) combining: total reports, harmful message ratio, highest risk seen, average risk, and temporal escalation.
- **Behavior Levels** — `Safe` → `Watch` → `High` → `Critical`, with AI-generated recommendation text.
- **Explainability** — Each profile includes a human-readable list of score factors explaining why the actor was escalated.
- **Behavioral Timeline** — A chronological log of level changes with timestamps and reasons.
- **Actor Profile Drawer** — Full-screen slide-in panel in the dashboard showing all profile fields, statistics, category distribution, and timeline.

---

### 6. AI-Powered Chatbot (Dual Persona)

An embedded conversational AI assistant powered by **Groq API** (`llama-3.1-8b-instant`):

| Persona | Audience | Scope |
|---|---|---|
| **User (Victim) Persona** | End users | Empathetic guidance on reporting, safety steps, and legal options |
| **Analyst Persona** | Admins / Moderators | Tactical investigation support based on fusion evidence, behavioral profiles, and risk scores |

- Context-aware: the chatbot receives the current prediction result as context.
- File upload support: users can attach documents (PDF, TXT, images, etc.) for AI-assisted analysis.
- Domain-restricted: the chatbot will only answer questions related to cyber safety, digital forensics, and the current incident — it refuses off-topic queries.

---

### 7. Incident Complaint System

Users can file structured complaints through the platform:

- **Complaint Queue** — Admin-visible queue of all user-submitted complaints.
- **Groq-Powered Summarization** — `summarize.py` generates a structured incident summary (description, severity tier, suggested action) from the complaint content using Groq LLM.
- **Duplicate / Similar Report Detection** — `sentence-transformers` (`all-MiniLM-L6-v2`) detects semantically similar existing reports to prevent duplicate entries.
- **Self-Serve Isolation** — Reports submitted by users through the public portal are tagged `source: self_serve` and excluded from admin statistics and behavioral profiling, maintaining clean data separation.

---

### 8. Forensic Dashboard (Admin / SOC Interface)

A full **Cyber Security Operations Center** interface for trust & safety teams:

- **Organization Dashboard** — High-level KPI stats (total reports, safe/flagged breakdown, high-risk count, avg confidence, avg risk score, conversations analyzed, evidence plans generated).
- **Advanced Analytics** — Category distribution charts, confidence distribution, risk tier breakdown, and multi-label co-occurrence.
- **Trend Chart** — Daily report volume over time with anomaly highlighting (Z-score based).
- **Moderator Queue** — Paginated, searchable, and filterable tables for individual message reports and full conversation logs. Supports filtering by risk level and category.
- **Incident Intelligence Panel** — Slide-in flyout with full incident details: fusion evidence, token heatmap, threat intel findings, typosquatting alerts, PII categories detected, evidence plan, and victim guidance.
- **Conversation Details Drawer** — Full conversation replay with per-message risk scores, classification badges, and timeline.
- **Behavioral Intelligence** — Actor profile table with sortable scores and levels, plus the full Actor Profile Drawer.
- **Complaint Queue** — Dedicated view for user-filed complaints with AI-generated summaries.

---

### 9. Real-Time Chrome Extension

A lightweight Manifest V3 Chrome extension providing real-time threat scanning in the browser:

- **Viewport-Only Scanning** — Uses `IntersectionObserver` to scan only messages currently visible in the user's viewport. No message history is stored or sent in bulk.
- **Inline Threat Badges** — Injects color-coded risk badges directly into the DOM of supported platforms.
- **Supported Platforms** — Gmail, WhatsApp Web (extensible to others via content script selectors).
- **Secure Authentication** — Backend communication authenticated via `X-Extension-Api-Key` header.
- **Privacy-First** — No browsing history stored. No background page mass-scanning. Scan is triggered only by visibility.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                        │
│  React SPA (Vite)          Chrome Extension (MV3)       │
│  ┌─────────────────┐       ┌────────────────────────┐   │
│  │  Threat Hunt    │       │  Content Script        │   │
│  │  SOC Dashboard  │       │  IntersectionObserver  │   │
│  │  Chatbot Panel  │       │  Inline Badge Injector │   │
│  └────────┬────────┘       └───────────┬────────────┘   │
└───────────┼───────────────────────────┼─────────────────┘
            │ REST API (JSON)           │ X-Extension-Api-Key
            ▼                           ▼
┌─────────────────────────────────────────────────────────┐
│                    FLASK BACKEND                        │
│                                                         │
│  Blueprints: public_bp | admin_bp | complaints_bp       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │           PREDICTION PIPELINE                   │    │
│  │                                                 │    │
│  │  Input → Preprocess → PrimaryModelAdapter       │    │
│  │         (DistilBERT or TF-IDF baseline)         │    │
│  │              ↓                                  │    │
│  │  HeuristicMultiLabelAdapter (17 rule classes)   │    │
│  │              ↓                                  │    │
│  │  ThreatIntelAdapter (URLs, WHOIS, HIBP, SE)     │    │
│  │              ↓                                  │    │
│  │  Noisy-OR Risk Score Fusion                     │    │
│  │              ↓                                  │    │
│  │  PII Masking → Response                         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Services: PredictionService | AdminService             │
│            BehaviorService | EvidenceService            │
│            GuidanceService | AuthService                │
│            SummarizeService (Groq)                      │
│                                                         │
│  ML: predict_transformer.py | predict.py                │
│      explain_transformer.py (Captum IG)                 │
│      transcribe.py (Whisper) | ocr.py (EasyOCR)         │
│      similarity.py (SentenceTransformers)               │
│      chatbot.py (Groq llama-3.1-8b-instant)             │
│      behavior.py (Actor scoring)                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  PERSISTENCE LAYER                      │
│                                                         │
│  MongoDB Atlas (primary) / In-memory fallback           │
│  Collections: reports | conversations | profiles        │
│               complaints                                │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Framework | Python 3.10+, Flask 3.0, Flask-CORS, Flask-Limiter |
| Primary ML Model | HuggingFace `distilbert-base-uncased` (fine-tuned), PyTorch |
| Baseline ML Model | scikit-learn (TF-IDF + Logistic Regression) |
| Explainability | Captum (Integrated Gradients), token-level attribution |
| Audio Transcription | OpenAI Whisper (`base` model, ~150MB) |
| OCR | EasyOCR, OpenCV (`opencv-python-headless`) |
| Semantic Similarity | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| LLM Integration | Groq API (`llama-3.1-8b-instant`) |
| Authentication | PyJWT (HS256), RBAC middleware decorators |
| Rate Limiting | Flask-Limiter 3.8 |
| Database | MongoDB Atlas (via `pymongo[srv]`), in-memory fallback |
| WHOIS | `python-whois` |
| Caching | `cachetools` TTLCache (10-minute TTL for threat intel) |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18, Vite 5 |
| Styling | Tailwind CSS (custom cyber theme), Vanilla CSS for global tokens |
| Charts | Recharts |
| Icons | Lucide React |
| Fonts | Inter (UI), JetBrains Mono (data/terminal) |
| Design System | Glassmorphism, neon cyan/purple accent palette, semantic risk colors |

### Chrome Extension
| Component | Technology |
|---|---|
| Manifest Version | V3 |
| Content Script | Vanilla JavaScript, `IntersectionObserver` API |
| Authentication | `X-Extension-Api-Key` header |

---

## Project Structure

```
online-harassment-detection/
├── backend/
│   ├── app.py                    # Flask entry point, blueprint registration
│   ├── extensions.py             # Flask-Limiter singleton
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── api/
│   │   ├── routes_public.py      # Public prediction endpoints + chatbot
│   │   ├── routes_admin.py       # JWT-protected admin endpoints
│   │   ├── routes_complaints.py  # Complaint submission/retrieval
│   │   ├── routes_auth.py        # Auth utility routes
│   │   └── dependencies.py       # @token_required, @require_role decorators
│   ├── ml/
│   │   ├── predict_transformer.py  # DistilBERT inference
│   │   ├── predict.py              # Baseline TF-IDF model
│   │   ├── preprocess.py           # Text normalization
│   │   ├── explain.py              # LIME/heuristic explain
│   │   ├── explain_transformer.py  # Captum Integrated Gradients
│   │   ├── behavior.py             # Actor behavior score calculation
│   │   ├── chatbot.py              # Groq LLM chat interface
│   │   ├── summarize.py            # Groq complaint summarization
│   │   ├── transcribe.py           # Whisper audio→text
│   │   ├── ocr.py                  # EasyOCR screenshot→text
│   │   ├── similarity.py           # Semantic duplicate detection
│   │   └── adapters/
│   │       ├── base.py             # Abstract adapter interface
│   │       ├── heuristic.py        # Multi-label heuristic adapter
│   │       ├── conversation.py     # Conversation-level adapter
│   │       └── threat_intel.py     # URL/WHOIS/HIBP/SE intel + PII masking
│   ├── services/
│   │   ├── prediction_service.py   # Orchestrates full prediction pipeline
│   │   ├── admin_service.py        # Stats, reports, conversations, anomalies
│   │   ├── behavior_service.py     # Actor profile CRUD + scoring
│   │   ├── auth_service.py         # JWT issuance and verification
│   │   ├── evidence_service.py     # Evidence playbook selection
│   │   ├── guidance_service.py     # Victim safety guidance
│   │   ├── parsers.py              # WhatsApp/Instagram file parsers
│   │   └── email_service.py        # (Reserved for future notifications)
│   ├── core/
│   │   ├── database.py             # MongoDB + in-memory DB abstraction
│   │   ├── config.py               # App configuration
│   │   ├── exceptions.py           # Custom exception classes
│   │   └── logger.py               # Logging setup
│   ├── config/
│   │   └── evidence_playbooks.json # Per-category forensic action plans
│   ├── models/                     # Fine-tuned model weights (git-ignored)
│   └── test_security.py            # RBAC + data isolation regression tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # SPA router and layout shell
│   │   ├── index.css               # Global cyber theme design tokens
│   │   ├── components/
│   │   │   ├── AnalyzeForm.jsx             # Threat Hunt console (main form)
│   │   │   ├── Dashboard.jsx               # Dashboard sub-tab router
│   │   │   ├── Header.jsx / Sidebar.jsx    # Navigation chrome
│   │   │   ├── analysis/                   # InstantAnalysisForm
│   │   │   ├── auth/                       # LoginForm
│   │   │   ├── chatbot/                    # ChatbotPanel
│   │   │   ├── complaints/                 # MyHistory (user complaint log)
│   │   │   ├── common/                     # Card, LoadingState, HowItWorks
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardStats.jsx         # KPI stat cards
│   │   │   │   ├── AdvancedAnalytics.jsx       # Category/confidence charts
│   │   │   │   ├── TrendChart.jsx              # Daily trend + anomalies
│   │   │   │   ├── ModeratorQueue.jsx          # Incident tables
│   │   │   │   ├── IncidentIntelligencePanel.jsx # Incident detail flyout
│   │   │   │   ├── ConversationDetailsDrawer.jsx # Conversation replay
│   │   │   │   ├── BehavioralIntelligence.jsx  # Actor profile table
│   │   │   │   └── ActorProfileDrawer.jsx      # Actor detail slide-in
│   │   │   └── prediction/
│   │   │       ├── RiskBadge.jsx               # Color-coded risk indicator
│   │   │       ├── ThreatIntelligenceCard.jsx  # Threat intel findings
│   │   │       ├── TokenHeatmap.jsx            # Captum attribution heatmap
│   │   │       ├── ExplainPanel.jsx            # Explainability factors
│   │   │       ├── EvidenceViewer.jsx          # Evidence action plan
│   │   │       ├── GuidancePanel.jsx           # Victim safety guidance
│   │   │       └── PersonalizedSafetyPlan.jsx  # Structured safety cards
│   │   ├── hooks/
│   │   │   ├── useAuth.js                   # JWT auth state hook
│   │   │   └── useAdminData.js              # Dashboard data fetch hook
│   │   └── api/                             # API client utilities
├── extension/
│   ├── manifest.json               # Chrome Extension Manifest V3
│   ├── content.js                  # DOM injection + IntersectionObserver
│   ├── background.js               # Service worker
│   ├── popup.html / popup.js       # Extension settings popup
│   └── content.css                 # Badge styling
├── docker-compose.yml
├── docs/
└── notebooks/                      # Training notebooks (Colab-ready)
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (or run without it — the app has a full in-memory fallback)
- (Optional) GPU with CUDA for faster model inference

---

### 1. Backend Setup

```bash
# Clone the repository
git clone <repo-url>
cd online-harassment-detection

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# → Edit .env with your keys (see Environment Variables section)

# Start the server
python app.py
# Backend runs at http://localhost:5000
```

**First-run note:** On first startup, the following models are downloaded automatically:
- OpenAI Whisper `base` (~150 MB) — audio transcription
- `all-MiniLM-L6-v2` (~22 MB) — semantic similarity

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Dashboard runs at http://localhost:5173
```

**Production build:**
```bash
npm run build
# Output in frontend/dist/
```

---

### 3. Chrome Extension Setup

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (toggle, top right)
3. Click **Load unpacked** → select the `extension/` folder
4. Click the ShieldAI icon in the Chrome toolbar
5. Enter your `EXTENSION_API_KEY` from `backend/.env`

The extension will now scan visible messages on supported sites (Gmail, WhatsApp Web).

---

## Environment Variables

Create `backend/.env` from the following template:

```env
# ── Database ──────────────────────────────────────────────────────
# MongoDB Atlas connection string. If omitted, the app uses an
# in-memory store (data is lost on restart).
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/shieldai

# ── Authentication ────────────────────────────────────────────────
# Secret key for JWT signing. Use a long, random string.
JWT_SECRET_KEY=your-very-secure-random-secret

# ── Admin Credentials ─────────────────────────────────────────────
# Seeded admin user. Change before deploying to production.
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# ── Threat Intelligence ───────────────────────────────────────────
# Google Safe Browsing API v4 key (optional but recommended).
GOOGLE_SAFE_BROWSING_KEY=your-gsb-api-key

# Have I Been Pwned API key (optional).
HIBP_API_KEY=your-hibp-api-key

# ── AI / LLM ──────────────────────────────────────────────────────
# Groq API key — required for chatbot and complaint summarization.
GROQ_API_KEY=your-groq-api-key

# ── Chrome Extension ──────────────────────────────────────────────
# Secret key the Chrome extension sends as X-Extension-Api-Key.
EXTENSION_API_KEY=your-extension-api-key

# ── Explainability (Optional) ─────────────────────────────────────
# HuggingFace token — required only if using gated models.
HF_TOKEN=your-hf-token
```

**Security rules:**
- Never commit `.env` to version control (it is in `.gitignore`).
- Rotate `JWT_SECRET_KEY` if you suspect it has been exposed.
- All keys are validated at startup; missing optional keys degrade gracefully (feature is disabled, not crashed).

---

## API Reference

### Public Endpoints (No Auth Required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/predict` | Analyze a single text message |
| `POST` | `/predict/conversation` | Analyze a full conversation (list of messages) |
| `POST` | `/predict/image` | OCR + classify a screenshot |
| `POST` | `/predict/audio` | Transcribe + classify an audio/video file |
| `POST` | `/predict/file` | Parse and analyze a WhatsApp/Instagram export file |
| `POST` | `/chat` | Send a message to the ShieldAI chatbot |
| `POST` | `/complaints` | Submit a user complaint |
| `GET` | `/complaints` | Get complaints for the authenticated user |

### Admin Endpoints (JWT Required)

| Method | Endpoint | Required Role | Description |
|---|---|---|---|
| `POST` | `/admin/login` | Public | Authenticate and receive JWT |
| `GET` | `/admin/stats` | Admin, Moderator, Viewer | Platform-wide KPI statistics |
| `GET` | `/admin/reports` | Admin, Moderator, Viewer | Paginated message report list |
| `GET` | `/admin/conversations` | Admin, Moderator, Viewer | Paginated conversation log |
| `GET` | `/admin/profiles` | Admin, Moderator, Viewer | Actor behavioral profiles |
| `GET` | `/admin/analytics` | Admin, Moderator, Viewer | Category/confidence breakdowns |
| `GET` | `/admin/daily-counts` | Admin, Moderator, Viewer | Daily report volume for trend chart |
| `GET` | `/admin/anomalies` | Admin, Moderator, Viewer | Z-score anomaly detection results |
| `GET` | `/admin/complaints` | Admin, Moderator | All user-submitted complaints |
| `POST` | `/admin/ban` | Admin only | Flag an actor as banned |
| `GET` | `/admin/audit` | Admin only | Security audit log |

---

## Role-Based Access Control

JWT tokens include a `role` claim. All admin routes are enforced by `@token_required` and `@require_role()` decorators in `api/dependencies.py`.

| Role | Dashboard Access | Can Read Reports | Can Ban Actors | Can View Audit Log |
|---|---|---|---|---|
| **Admin** | Full | ✅ | ✅ | ✅ |
| **Moderator** | Full | ✅ | ❌ | ❌ |
| **Viewer** | Read-only | ✅ | ❌ | ❌ |
| **User** | Threat Hunt + My History | Own only | ❌ | ❌ |
| **Guest** | Threat Hunt only | None | ❌ | ❌ |

**Data Isolation:** Reports submitted through the self-serve portal (`source: self_serve`) are strictly excluded from admin statistics, behavioral profiling, and the moderator queue. Users can only retrieve their own reports.

---

## Security & Privacy

| Control | Implementation |
|---|---|
| **JWT Authentication** | HS256-signed tokens, enforced on every admin route |
| **RBAC** | Decorator-based role enforcement, roles embedded in JWT claims |
| **PII Masking** | All API responses pass through `mask_pii()` before returning to client |
| **Rate Limiting** | Flask-Limiter on public prediction endpoints to prevent abuse |
| **Data Isolation** | `source != self_serve` filter on all admin aggregations |
| **Extension Auth** | `X-Extension-Api-Key` header validated on extension-facing routes |
| **No Extension Storage** | Chrome extension stores no messages; scans only the live viewport |
| **Stateless Analysis** | `predict` endpoints can run without database persistence |
| **Input Sanitization** | File upload validation by extension and size; `secure_filename` used |
| **External API Timeouts** | All WHOIS/HIBP/GSB calls wrapped in timeout + fallback |

---

## Running Tests

### Backend Security & RBAC Regression Suite

```bash
cd backend
# Ensure the Flask server is running on port 5000 first:
# python app.py

python -m pytest test_security.py test_format_baseline.py -v
```

**Expected output:**
```
test_security.py::test_rbac_admin_endpoints         PASSED
test_security.py::test_private_analysis_persist     PASSED
test_security.py::test_self_serve_isolation         PASSED
test_security.py::test_data_ownership               PASSED
test_security.py::test_actor_profiling              PASSED
test_security.py::test_admin_reports_non_self_serve PASSED
6 passed in ~152s
```

### Frontend Build Verification

```bash
cd frontend
npm run build
# Expected: ✓ 2012 modules transformed, exit code 0
```

---

## Docker Deployment

A `docker-compose.yml` is provided for containerized deployment:

```bash
# From the project root
docker-compose up --build
```

| Service | Port | Description |
|---|---|---|
| `backend` | `5000` | Flask API server (Gunicorn in production) |
| `frontend` | `3000` | React SPA served via Nginx |

**Note:** Ensure `backend/.env` is populated before running Docker. Model weights in `backend/models/` are mounted as a volume so they persist across container restarts.

---

## Chrome Extension

### Supported Sites

| Platform | Selector Strategy |
|---|---|
| WhatsApp Web | `.message-in`, `.message-out` DOM selectors |
| Gmail | Message body element selectors |

### How It Works

1. The content script uses `IntersectionObserver` to watch message elements entering the viewport.
2. When a message becomes visible, it extracts the text and sends it to `POST /predict` with the `X-Extension-Api-Key` header.
3. The response risk level is used to inject a small, non-intrusive color-coded badge into the message DOM.
4. The badge is removed if the message leaves the viewport, keeping the UI clean.

---

## Acknowledgements

- [HuggingFace Transformers](https://huggingface.co/docs/transformers) — DistilBERT
- [Captum](https://captum.ai/) — Model interpretability
- [OpenAI Whisper](https://github.com/openai/whisper) — Audio transcription
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — Screenshot text extraction
- [Groq](https://groq.com/) — LLM inference (chatbot + summarization)
- [Google Safe Browsing](https://developers.google.com/safe-browsing) — URL threat intel
- [Have I Been Pwned](https://haveibeenpwned.com/API/v3) — Breach detection

---

*ShieldAI is built for educational and trust & safety research purposes. All threat detection is probabilistic and should be reviewed by a qualified investigator before any enforcement action is taken.*
