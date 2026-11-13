# ShieldAI — Comprehensive Viva Defense, Architecture & Technical Guide

> **Project Title:** ShieldAI — Production-Grade Cyber Threat Intelligence & Online Harassment Detection Platform  
> **Degree:** Master of Computer Applications (MCA) Final-Year Capstone Project  
> **Student:** Jayanth C  
> **Architecture:** Neurosymbolic Hybrid (Fine-Tuned DistilBERT + Heuristic Rules + Captum XAI + Multi-Provider LLM Router)

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Why Did You Choose This Project?](#2-why-did-you-choose-this-project)
3. [Why Is It Built Like This? (Architectural Justification)](#3-why-is-it-built-like-this-architectural-justification)
4. [The Critical Examiner Question: Google & ChatGPT Already Exist — Why Build This?](#4-the-critical-examiner-question-google--chatgpt-already-exist--why-build-this)
5. [Is This System Useful for Both Organizations and the Public?](#5-is-this-system-useful-for-both-organizations-and-the-public)
6. [Complete Tech Stack Breakdown](#6-complete-tech-stack-breakdown)
7. [In-Depth Technical Viva Questions by Technology](#7-in-depth-technical-viva-questions-by-technology)
   - [Frontend: React 18, Vite & TailwindCSS](#frontend-react-18-vite--tailwindcss)
   - [Backend: Python Flask, WSGI & Blueprints](#backend-python-flask-wsgi--blueprints)
   - [Machine Learning & Transformers: DistilBERT & Tokenization](#machine-learning--transformers-distilbert--tokenization)
   - [Explainable AI: Captum & Integrated Gradients](#explainable-ai-captum--integrated-gradients)
   - [Security & Authentication: PyJWT & Flask-Limiter](#security--authentication-pyjwt--flask-limiter)
   - [Database & Storage: SQLAlchemy ORM & SQLite](#database--storage-sqlalchemy-orm--sqlite)
   - [Browser Integration: Chrome Manifest v3](#browser-integration-chrome-manifest-v3)
8. [Top 7 Examiner "Trap" Questions & Hard Loopholes](#8-top-7-examiner-trap-questions--hard-loopholes)
9. [System Architecture Diagrams](#9-system-architecture-diagrams)
10. [5-Minute Flawless Live Demo Flow](#10-5-minute-flawless-live-demo-flow)

---

## 1. Executive Summary & Problem Statement

Online harassment, sextortion, job recruitment scams, and cyberbullying represent an escalating global crisis. In India alone, cyber extortion and digital fraud cases have increased dramatically under sections 66E, 67, and 503 of the Information Technology Act.

Existing solutions suffer from three fundamental deficiencies:
1. **The "Notebook Trap":** Academic AI models exist as standalone scripts with no operational pipeline, user interface, or evidence preservation workflow.
2. **The "Black-Box Trap":** Standard deep learning classifiers output probability scores without explaining *why* an incident was flagged, making them useless in forensic or legal proceedings.
3. **The "Passive Filter Trap":** Most filters simply block bad words. They do not calculate conversation escalation over time, profile repeat offenders across independent incidents, or provide trauma-informed emergency guidance to panicked victims.

**ShieldAI** solves these problems by delivering an end-to-end, privacy-first **Cyber Threat Intelligence & Incident Response Platform**. It combines fine-tuned transformer classification (`DistilBERT`), deterministic heuristic pattern engines, Explainable AI (`Captum`), a multi-provider crisis assistant (Groq, Anthropic, and offline rules), and a Security Operations Center (SOC) dashboard.

---

## 2. Why Did You Choose This Project?

### The Personal & Social Motivation
> *"Examiner Sir/Madam, I chose this project because digital abuse and cyber extortion are urgent human safety problems where computer applications can make an immediate, tangible difference."*

Three specific motivations drove this project:
1. **The Victim's 'Panic Window':** When someone receives a sextortion threat or financial extortion demand at 2:00 AM, police cyber cells and college grievance offices are unavailable. Victims frequently panic, comply with ransom demands, or delete their chat logs in distress, destroying the legal evidence needed to prosecute offenders. I wanted to build a trauma-informed first-responder tool that calmly prevents victims from paying, guides them through evidence preservation, and connects them with official Indian statutory resources.
2. **The Failure of General-Purpose AI:** Pasting private blackmail chats, intimate imagery demands, phone numbers, or bank accounts into public cloud tools like ChatGPT or Google exposes highly sensitive Personally Identifiable Information (PII) to third-party data collection. Furthermore, generic models hallucinate US-centric guidance (such as calling 911) rather than statutory Indian reporting under the IT Act.
3. **Academic & Engineering Depth:** As an MCA student, I wanted to build a capstone that bridges cutting-edge deep learning with production-grade full-stack engineering, secure API architecture, database integrity, and forensic transparency.

---

## 3. Why Is It Built Like This? (Architectural Justification)

When an examiner asks why the system is structured in its current form, emphasize these **5 deliberate design decisions**:

```
+------------------------------------------------------------------------+
|                            ShieldAI Stack                              |
|                                                                        |
|   Frontend (React + Vite)  <--->  Browser Extension (Manifest v3)       |
|                             |                                          |
|                             v                                          |
|                    Backend API (Flask REST)                            |
|                             |                                          |
|    +------------------------+-----------------------+                  |
|    |                        |                       |                  |
|    v                        v                       v                  |
| Hybrid Engine         Explainable AI        Multi-Provider Chat        |
| (DistilBERT + Rules)    (Captum XAI)        (Groq/Claude/Offline Rules)|
+------------------------------------------------------------------------+
```

### 1. Why a "Hybrid Fusion" Architecture instead of pure Deep Learning?
* **Problem with Pure Deep Learning:** Neural models are computationally expensive, have higher latency, and can be blind to exact structural signatures like shortened phishing URLs (`bit.ly`), suspicious Indian phone numbers (`+91`), or UPI ID formats (`name@okaxis`).
* **Problem with Pure Rule Engines:** Keyword and regex matching fails completely on subtle intimidation, indirect threats, sarcasm, and grammatical context.
* **ShieldAI Solution:** A **Dual-Path Fusion Engine**. Fast deterministic heuristics catch structured threat indicators in under 5 milliseconds. A fine-tuned DistilBERT transformer evaluates semantic and contextual toxicity in sub-80ms. The signals are fused to achieve both high throughput and high precision.

### 2. Why Integrate Explainable AI (Captum Integrated Gradients)?
* In legal, forensic, and disciplinary investigations, a "black-box" probability score is legally invalid. An investigator cannot submit: *"The AI model says there is an 88% chance of harassment."*
* ShieldAI integrates **Captum Integrated Gradients** to compute token-level attribution values. Words that drove the threat score are highlighted visually with mathematically grounded attribution scores, creating defensible forensic reports.

### 3. Why a Web Portal Combined with a Chrome Extension?
* Harassment happens where users browse: social media feeds, webmail, and web messaging platforms.
* The **Manifest v3 Chrome Extension** passively scans live webpage elements and provides non-intrusive risk badges. The **React Web Portal** provides the comprehensive Security Operations Center (SOC) dashboard for deep scanning, chat export analysis, case triage, and offender intelligence.

### 4. Why an Offline-First Multi-Provider Chatbot Architecture?
* Cloud LLM APIs (Groq, Anthropic) can run out of quota, encounter rate-limits (HTTP 429), or fail during network outages. In a digital crisis, the system cannot freeze or crash.
* ShieldAI employs an **automatic multi-tier fallback**: if cloud LLMs are unavailable, the assistant seamlessly switches to a grounded, deterministic rule-based knowledge engine, surfacing a clear status badge to the user.

### 5. Why Privacy-by-Design (PII Masking & Private Scan)?
* A safety system must never turn into a surveillance tool.
* ShieldAI implements automated regex PII sanitization (redacting phone numbers, email addresses, Aadhaar, and credit card patterns) and provides a **"Private Scan"** toggle that guarantees no user submission is persisted to the database.

---

## 4. The Critical Examiner Question: Google & ChatGPT Already Exist — Why Build This?

> **Examiner Question:** *"Google Perspective API, OpenAI ChatGPT, and Google Gemini already detect toxic text. Why did you spend months building ShieldAI? Where is this actually more useful?"*

### The 1-Line Hook
> *"Examiner Sir/Madam, Google and ChatGPT are **general foundation models**, whereas ShieldAI is a **specialized, privacy-first Incident Response & Forensic Triage Platform**."*

### Key Differentiators Table

| Architectural Dimension | Generic AI (ChatGPT / Google) | ShieldAI Platform |
| :--- | :--- | :--- |
| **Privacy & Data Sovereignty** | Transmits sensitive blackmail text & PII to public US cloud servers. | Runs on-premise; includes automatic PII masking and a "Private Scan" zero-storage mode. |
| **Multi-Party Chat Exports** | Evaluates single sentences in isolation; cannot parse 50 WhatsApp messages. | Parses multi-party chat exports, **isolates the culprit** (e.g. "Sam") from innocent bystanders, and computes escalation velocity. |
| **Repeat Offender Profiling** | Has zero memory across independent incidents. | Normalizes domains, handles, and phone numbers to track **repeat offender hit counts** across different victims. |
| **Forensic Transparency (XAI)** | Black box; outputs conversational text without audit trails. | Uses **Captum Integrated Gradients** to mathematically attribute risk weights to individual tokens. |
| **Statutory Indian Mapping** | Hallucinates generic or US-centric advice (e.g. "Call 911"). | Directly integrated with **Helpline 1930, StopNCII.org, 112, and cybercrime.gov.in** under the IT Act. |
| **Operational Workflow (SOC)** | No triage interface, status workflows, or queues. | Full **Security Operations Center** with Report Queue (Messages & Conversations tabs), case assignment, and trend charts. |
| **Offline Cost & Resilience** | Charges per API token; completely dead without internet access. | Lightweight DistilBERT + Heuristic engine runs locally on commodity CPU with **zero token costs**. |

---

## 5. Is This System Useful for Both Organizations and the Public?

> **Examiner Question:** *"Is this system built for ordinary citizens or for enterprise organizations? Can one platform serve both?"*

**Answer:** Yes. ShieldAI is built on a **Dual-Sided Architecture** that connects the general public to organizational incident response:

```
[ General Public / Citizens ]  --->  [ Public Scan & Private Assist ]
                                              |
                                              v (If consented / public report)
[ Enterprise / Campus SOC ]    <---  [ Moderator Queue & Offender Intel ]
```

### A. Value for the General Public (Citizens & Students)
1. **Immediate Crisis First-Response:** Provides 24/7 de-escalation when institutions are closed.
2. **Anonymous & Private Reporting:** Citizens can check threats safely via Private Scan without fear of surveillance.
3. **Evidence Preservation Playbook:** Generates structured checklists so victims do not inadvertently destroy evidence before reporting.
4. **Non-Consensual Image Protection:** Connects victims of intimate image extortion directly to **StopNCII.org** to prevent image distribution before it occurs.

### B. Value for Organizations (Colleges, Enterprises, Social Platforms)
1. **Statutory Compliance:** Fulfills mandates under India's **IT Rules 2021 (Intermediary Guidelines)** and university **UGC/AICTE Anti-Ragging regulations**.
2. **Turnkey Incident Triage (SOC):** Small-to-medium platforms that cannot afford a multimillion-dollar trust & safety team get an out-of-the-box case management system.
3. **Repeat Offender Blacklisting:** Identifies persistent harassers operating across different student batches or departments.
4. **Data Retention & Privacy Purge:** Automatically schedules anonymization and statutory record purging in compliance with the **Digital Personal Data Protection (DPDP) Act**.

---

## 6. Complete Tech Stack Breakdown

| Layer | Technologies Used | Justification |
| :--- | :--- | :--- |
| **Frontend UI** | React 18, Vite 5, TailwindCSS, Lucide Icons | Component-driven architecture, ultra-fast Hot Module Replacement (HMR), responsive cybersecurity theme. |
| **Data Visualization** | Recharts (ResponsiveContainer, BarChart, LineChart) | Interactive incident frequency, category distribution, and risk trend charting in the SOC. |
| **Backend Gateway** | Python 3.10+, Flask 3.0, Werkzeug | Lightweight, micro-framework providing low overhead, fine-grained WSGI request lifecycle control. |
| **API Security** | PyJWT (HS256), Flask-Limiter, Flask-CORS | Token-based Role-Based Access Control (Admin, Moderator, Viewer, User), brute-force DoS protection. |
| **Database & ORM** | SQLAlchemy 2.0 ORM, SQLite 3 (`shieldai.db`) | Portability and embedded deployment with complete relational modeling; easily swappable to PostgreSQL. |
| **Neural NLP** | DistilBERT (`distilbert-base-uncased`), PyTorch, Transformers | Pre-trained contextual Transformer fine-tuned for multi-label toxicity, hate speech, and physical threat classification. |
| **Baseline Benchmark** | Scikit-Learn (TF-IDF Vectorizer + Logistic Regression) | Empirical academic benchmark model used to validate the accuracy gains of the Transformer. |
| **Explainable AI (XAI)** | Captum (Integrated Gradients) | Axiomatic attribution method providing token-level saliency scores for forensic explainability. |
| **Multi-Modal Ingestion** | `pypdf`, `pdfplumber`, RapidOCR, faster-whisper | Document parsing (PDF), optical character recognition for screenshots, and voice note transcription. |
| **LLM & Safety Assistant** | Groq API (`openai/gpt-oss-120b`), Anthropic API (`claude-haiku-5-5`), Offline Rules | Multi-provider LLM routing with sub-second inference and automatic failover to local deterministic rules. |
| **Browser Extension** | Chrome Manifest v3 (Service Worker, Content Script, Badges) | Live in-browser DOM element scanning and context badge rendering. |

---

## 7. In-Depth Technical Viva Questions by Technology

### Frontend: React 18, Vite & TailwindCSS

#### Q1. Why did you choose Vite instead of Create-React-App (CRA)?
* **Answer:** Create-React-App is deprecated and relies on Webpack, which bundles the entire application before serving, resulting in slow startup times. Vite uses **native ES Modules (ESM)** in the browser and pre-bundles dependencies with **esbuild** (written in Go, which is 10–100x faster than JavaScript-based bundlers). This provides instant dev server start and lightning-fast Hot Module Replacement (HMR).

#### Q2. How is navigation state preserved when a user refreshes (`Ctrl+R`)?
* **Answer:** Navigation state is synchronized across three tiers:
  1. The **URL Hash** (`window.location.hash`, e.g. `#incidents`, `#chat`).
  2. The **URL Pathname** (`window.location.pathname`).
  3. **`localStorage`** (`shieldai_active_tab`).
  When `App.jsx` mounts, `getInitialTab()` evaluates the URL and storage with alias normalization (`#queue` &rarr; `incidents`), ensuring the user stays exactly where they were upon refreshing.

#### Q3. How does React's Virtual DOM improve performance in ShieldAI?
* **Answer:** When real-time threat scores or queue updates arrive, updating the real DOM directly is computationally expensive. React maintains an in-memory Virtual DOM tree, computes the minimal diff using its **Reconciliation Algorithm (Fiber)**, and batches DOM writes in a single repaint pass.

---

### Backend: Python Flask, WSGI & Blueprints

#### Q1. Why Flask instead of Django or FastAPI?
* **Answer:**
  * **Django** is heavily opinionated and monolithic; its built-in admin, ORM, and template engine create unnecessary overhead for a decoupled REST API serving machine learning models.
  * **FastAPI** is asynchronous and excellent for pure I/O-bound microservices, but heavy PyTorch and transformer inference is **CPU-bound**. Running CPU-bound tensor operations in an async event loop can block the loop without multi-process workers.
  * **Flask** provides the ideal balance: a minimal, transparent WSGI micro-framework where we can explicitly control the request lifecycle, auth decorators, and model loading.

#### Q2. What are Flask Blueprints and why did you use them?
* **Answer:** Blueprints allow modular structuring of Flask applications into independent route packages. ShieldAI separates concerns into `routes_public.py` (scanning, file uploads, chat assist), `routes_admin.py` (triage queue, offender stats, retention), and `routes_auth.py` (registration and login), preventing a monolithic `app.py`.

---

### Machine Learning & Transformers: DistilBERT & Tokenization

#### Q1. Why DistilBERT over standard BERT or RoBERTa?
* **Answer:** Standard `bert-base-uncased` has 110 million parameters and requires significant memory and latency. DistilBERT uses **Knowledge Distillation** (a student-teacher training framework where a smaller model mimics the full output distribution of the larger model). DistilBERT has **40% fewer parameters (66M)**, runs **60% faster**, and retains **97% of BERT's language comprehension**, making it feasible to run on commodity CPUs without cloud GPUs.

#### Q2. What is WordPiece Tokenization and how does it prevent Out-Of-Vocabulary (OOV) errors?
* **Answer:** Traditional NLP tokenizes by whitespace or full words, failing when an attacker misidentifies or misspells words. DistilBERT uses **WordPiece tokenization**: it breaks unfamiliar words into common subword units prefixed by `##`. For example, an abusive misspelling like `"cyberharasser"` is broken into `['cyber', '##har', '##ass', '##er']`. The model derives semantic meaning from the constituent subwords, effectively eliminating OOV failures.

#### Q3. What is the loss function used during fine-tuning?
* **Answer:** For multi-label classification (where a message can be both a `Threat` and `Harassment` simultaneously), we use **Binary Cross-Entropy with Logits Loss (`BCEWithLogitsLoss`)** across each label independently, rather than Softmax/Cross-Entropy which forces mutually exclusive classes.

---

### Explainable AI: Captum & Integrated Gradients

#### Q1. What is the mathematical principle of Integrated Gradients?
* **Answer:** Integrated Gradients (Sundararajan et al., 2017) satisfies two fundamental axioms of attribution: **Completeness** and **Implementation Invariance**. It computes the path integral of gradients along the straight line from a baseline (neutral zero-embedding) $x'$ to the input embedding $x$:
$$\text{Attribution}_i(x) = (x_i - x'_i) \times \int_{0}^{1} \frac{\partial F(x' + \alpha(x - x'))}{\partial x_i} d\alpha$$
In practice, ShieldAI approximates this integral using Riemann summation over 20 discrete interpolation steps ($\alpha$).

#### Q2. Why is Integrated Gradients superior to attention map visualization?
* **Answer:** Attention weights show which tokens the model focused on in self-attention layers, but studies (e.g., Jain & Wallace, 2019) prove that **attention is not explanation**—high attention does not necessarily mean the token drove the final classification output. Integrated Gradients measures the true gradient of the output prediction with respect to the input embeddings, proving direct mathematical causality.

---

### Security & Authentication: PyJWT & Flask-Limiter

#### Q1. Why did you use JWT with HS256 and how do you prevent the `alg:none` vulnerability?
* **Answer:** JSON Web Tokens (JWT) provide stateless, decentralized authentication. In `backend/api/dependencies.py`, the decoding call explicitly pins the algorithm:
```python
jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
```
By explicitly passing `algorithms=["HS256"]`, PyJWT immediately rejects any maliciously crafted token that specifies `"alg": "none"` or public-key confusion attacks.

#### Q2. How does Flask-Limiter protect the machine learning pipeline?
* **Answer:** Machine learning inference is computationally expensive. Without rate limiting, an attacker could launch a Denial of Service (DoS) attack by sending 10,000 text analysis requests per minute, exhausting server CPU and RAM. `Flask-Limiter` enforces rate limits (e.g., 30 requests/minute for file scans, 120/minute for extension batches), returning HTTP 429 when limits are breached.

---

### Database & Storage: SQLAlchemy ORM & SQLite

#### Q1. How does SQLAlchemy ORM prevent SQL Injection attacks?
* **Answer:** SQLAlchemy uses **parameterized queries** and prepared statements. User inputs are never directly concatenated into raw SQL strings. Instead, user values are sent to the database engine separately as bind parameters, ensuring the database treats input strictly as literal data, never as executable SQL commands.

#### Q2. If an examiner argues SQLite is a toy database, what is your answer?
* **Answer:** *"Sir, SQLite is embedded directly within the process, eliminating network socket latency and making local edge deployment trivial. However, because we utilized **SQLAlchemy ORM models**, the database layer is completely decoupled. By modifying `DATABASE_URL` in `.env` to `postgresql://user:pass@host/db`, the application immediately connects to an enterprise PostgreSQL cluster without modifying a single line of application code."*

---

### Browser Integration: Chrome Manifest v3

#### Q1. What is the difference between Manifest v2 and Manifest v3?
* **Answer:** Manifest v3 enhances browser security and performance:
  1. **Background Service Workers:** Replaces persistent background pages with ephemeral service workers that spin down when idle, conserving system memory.
  2. **Prohibition of Remotely Hosted Code:** All extension logic must be packaged within the extension; no loading arbitrary remote scripts via `eval()`.
  3. **Content Script Isolation:** Content scripts run in an isolated world, preventing web pages from tampering with extension variables.

---

## 8. Top 7 Examiner "Trap" Questions & Hard Loopholes

### Loophole 1: "How do you handle intentional leetspeak and obfuscation (e.g., `k!ll y0u`)?"
* **Answer:** ShieldAI employs a multi-tier pre-processing pipeline:
  1. **Character normalization:** Converts Unicode homoglyphs and leetspeak numbers (`0` &rarr; `o`, `!` &rarr; `i`, `1` &rarr; `l`, `@` &rarr; `a`).
  2. **Repetition compression:** Collapses elongated words (`kiiiilllll` &rarr; `kill`).
  3. **WordPiece subwords:** DistilBERT decomposes residual variations into known subword embeddings.

### Loophole 2: "What dataset did you train on, and what were the evaluation metrics?"
* **Answer:** We utilized the **Davidson et al. benchmark dataset** (~25,000 tweets annotated for hate speech, offensive language, and benign text), enhanced with threat and scam datasets.
* **Evaluation Metrics:** Evaluated on an 80/10/10 train/val/test split. While the baseline TF-IDF + Logistic Regression model achieved ~89% accuracy, the fine-tuned DistilBERT achieved **0.93 Macro F1-score**, excelling on minority threat classes where simple accuracy is misleading due to class imbalance.

### Loophole 3: "What happens if PyTorch or GPU drivers fail to load on the host machine?"
* **Answer:** ShieldAI is built with an **Active Fault-Tolerant Fallback Architecture**. If PyTorch fails (e.g. missing DLLs, CPU memory pressure), `model_service.py` catches the exception, logs a warning, and **automatically degrades to the heuristic rule engine**. The application remains 100% operational with 0 downtime, displaying an `Engine: Rules` badge in the UI.

### Loophole 4: "What happens if a user submits a violent threat written in Hindi or Kannada?"
* **Answer:** ShieldAI follows a **"Fail-Closed" Safety Rule**. It natively detects Romanized Hinglish and Kannada slang. However, if text contains native non-Latin scripts (Devanagari, Kannada, Tamil, Arabic), the system **never outputs a false 'Safe' pass**. Instead, it flags the threat as **`UNVERIFIED / UNSUPPORTED`** and directs it to the moderation queue for human assessment.

### Loophole 5: "How do you prevent a harasser from discovering who reported them?"
* **Answer:** Public submissions are completely decoupled from victim identity. The portal supports **Private Scan**, which runs in-memory analysis without writing to the database. For logged complaints, all reporter identifiers are encrypted, PII is masked, and access is strictly gated behind JWT Role-Based Access Control (`Admin` and `Moderator` roles only).

### Loophole 6: "What if a user uploads a malicious script or 1GB file disguised as a PDF?"
* **Answer:** Guarded by three defense layers:
  1. **Extension validation:** Only permitted extensions (`ALLOWED_CHAT_FILE_EXTS`) are accepted.
  2. **File size guards:** Strict 50MB ceiling for documents and 10MB for images; larger payloads are rejected with HTTP 413.
  3. **Safe cleanup:** Uploads are written to temporary files with guaranteed deletion in Python `finally` blocks, preventing disk exhaustion.

### Loophole 7: "What are the limitations of this project, and what is your future roadmap?"
* **Answer:**
  1. **Audio Streams:** Currently transcribes uploaded voice notes; future scope includes real-time WebRTC audio call stream inspection.
  2. **Native Indic LLMs:** Upgrading from DistilBERT to **MuRIL** or **XLM-RoBERTa** for direct native script processing.
  3. **Federated Learning:** Enabling multiple university campuses to collaboratively train threat models without exchanging private student incident logs.

---

## 9. System Architecture Diagrams

### High-Level System Architecture
```mermaid
flowchart TD
    subgraph Clients["Clients & Ingestion Channels"]
        User[End User / Victim]
        Admin[SOC Analyst / Moderator]
        ChromeExt[Chrome Extension MV3]
        WebUI[React 18 + Vite SPA Portal]
    end

    subgraph BackendGateway["API Gateway & Security Layer (Flask :5000)"]
        API[Flask REST API Endpoints]
        Auth[JWT HS256 Authentication & RBAC]
        Limiter[Flask-Limiter Rate Guard]
        PIIMask[PII Sanitization & Masking Engine]
    end

    subgraph NeurosymbolicPipeline["ShieldAI Hybrid Detection Pipeline"]
        TextNorm[Text & Script Normalizer]
        DistilBERT[DistilBERT Neural Classifier]
        Heuristics[Heuristic Regex Rules Engine]
        CaptumXAI[Captum Explainable AI]
        Fusion[Decision Aggregator & Risk Calibrator]
    end

    subgraph IntelligenceCore["Threat Intelligence & Incident Management"]
        ChatParser[Multi-Party Chat Export Parser]
        OffenderIntel[Repeat Offender Intelligence]
        TriageQueue[Moderator Case Triage Queue]
    end

    subgraph SafetyAssistant["AI Cyber Safety Assistant (Multi-Provider Router)"]
        Router[LLM Provider Router]
        Groq[Groq API: openai/gpt-oss-120b]
        Claude[Anthropic API: claude-haiku-5-5]
        OfflineRules[Grounded Rule Fallback Engine]
        StatutoryGuidance[Statutory Safety Protocols]
    end

    subgraph PersistenceLayer["Persistence & Compliance Layer (SQLAlchemy ORM)"]
        SQLite[(SQLite Database: shieldai.db)]
        ReportsTab[Reports & Incident Evidence]
        OffendersTab[Repeat Offender Profiles]
        ConversationsTab[Conversations & Chat Exports]
        RetentionPurge[Data Retention & Privacy Purge]
    end

    User -->|Submit Text, Screenshot, PDF, Audio| WebUI
    Admin -->|Manage Queue & Offender Intel| WebUI
    User -->|Live DOM Inspection| ChromeExt
    
    WebUI -->|REST API Requests| API
    ChromeExt -->|Batch Scan Requests| API
    
    API --> Auth
    API --> Limiter
    API --> PIIMask

    PIIMask --> TextNorm
    TextNorm --> DistilBERT
    TextNorm --> Heuristics
    DistilBERT --> CaptumXAI
    
    DistilBERT --> Fusion
    Heuristics --> Fusion
    CaptumXAI --> Fusion

    PIIMask --> ChatParser
    ChatParser --> OffenderIntel
    Fusion --> TriageQueue

    WebUI <--> Router
    Router -->|Primary Provider| Groq
    Router -->|Secondary Provider| Claude
    Router -->|Offline Fallback| OfflineRules
    Router --> StatutoryGuidance

    Fusion --> SQLite
    OffenderIntel --> SQLite
    TriageQueue --> SQLite
    SQLite --> ReportsTab
    SQLite --> OffendersTab
    SQLite --> ConversationsTab
    SQLite --> RetentionPurge
```

### Database Entity-Relationship Diagram (SQLAlchemy ORM)
```mermaid
erDiagram
    users {
        int id PK
        string username UK
        string password_hash
        string role "Admin, Moderator, Viewer, User"
        datetime created_at
    }

    reports {
        string id PK "UUID"
        string text_full "Full input text"
        string primary_label "Harassment, Threat, Phishing, Scam, Safe, Unsupported"
        string category
        float threat_score
        float risk_score
        float confidence
        string severity_tier "Critical, High, Medium, Low, Unsupported"
        string safety_status "Safe, Flagged, Unsupported"
        string actor_id FK "Sender or Identifier"
        string source "platform, screenshot, document, chat_export"
        string status "open, reviewing, resolved, dismissed"
        string user_id FK
        json flagging_reasons
        json threat_intel
        json guidance
        string model_used
        boolean is_synthetic
        datetime created_at
    }

    offenders {
        int id PK "Auto Increment"
        string entity_type "sender, url, phone, email"
        string entity_value UK "Normalized domain, handle, or number"
        int hit_count "Cumulative incident frequency"
        float peak_risk
        float avg_risk
        string first_seen
        string last_seen
        json categories "Associated threat categories"
        json related_reports "List of linked Report UUIDs"
        string status "active, flagged, banned, monitored"
        json timeline "Dated incident events"
        boolean is_synthetic
    }

    conversations {
        string id PK "UUID"
        string primary_label
        string severity_tier
        float threat_score
        float conversation_risk
        float confidence
        string escalation_level "Critical, High, Medium, Low"
        float escalation_score "Conversation acceleration bonus"
        json messages "Parsed dialogue array with senders"
        json actor_attribution "Culprit isolation mapping"
        string source "chat_export"
        string user_id FK
        boolean is_synthetic
        datetime created_at
    }

    complaints {
        string id PK "UUID"
        string user_id FK
        string text "Masked citizen report"
        string category
        float threat_score
        string severity_tier
        string status "open, reviewing, resolved, dismissed"
        string evidence_file "Optional attachment path"
        json result_json
        boolean is_synthetic
        datetime created_at
    }

    profiles {
        int id PK "Auto Increment"
        string actor_id UK "Unique actor handle/ID"
        int total_reports
        int safe_messages
        int harmful_messages
        float highest_risk
        float avg_risk
        float behavior_score
        string behavior_level "Safe, Suspicious, Malicious"
        string recommendation
        json timeline
        string status
    }

    audit_logs {
        int id PK "Auto Increment"
        string action "purge, status_change, export, login"
        string details "Operation metadata"
        string performed_by "User identity"
        datetime timestamp
    }

    users ||--o{ reports : "submits or reviews"
    users ||--o{ complaints : "files"
    reports }o--o{ offenders : "links to entity"
    conversations ||--o{ offenders : "identifies culprits"
    reports }o--|| profiles : "aggregates into profile"
```

---

## 10. 5-Minute Flawless Live Demo Flow

To achieve top marks during your live evaluation, execute this exact 5-minute demonstration:

```
[0:00 - 1:00] Public Scan & XAI Attribution
      |
[1:00 - 2:00] WhatsApp Multi-Party Chat Export & Culprit Isolation
      |
[2:00 - 3:00] Security Operations Center (SOC) & Moderator Queue
      |
[3:00 - 4:00] Repeat Offender Intelligence & Domain Normalization
      |
[4:00 - 5:00] AI Assistant Trauma Support & Automated Pytest Suite
```

1. **Minute 1 — Public Scan & Captum Token Attribution:**
   - Navigate to `http://localhost:5173/#analyze`.
   - Paste a high-risk sextortion sample: *"I recorded you on webcam. Pay 500 dollars in Bitcoin within 24 hours or I send it to your family."*
   - Show the dynamic **Risk Gauge** animate to Critical/High risk.
   - Point to the **Captum Token Attribution** box: show how `"pay"`, `"500 dollars"`, `"Bitcoin"`, and `"family"` are highlighted in red, proving explainable AI.

2. **Minute 2 — Multi-Party Chat Export & Culprit Isolation:**
   - In the Scan form, upload or paste the 7-message WhatsApp conversation containing participants **Raj, Priya, and Sam**.
   - Show how the parser computes a conversation escalation bonus and **isolates Sam as the culprit**, while identifying Raj and Priya as clean participants.

3. **Minute 3 — Security Operations Center (SOC) & Report Queue:**
   - Log in as Administrator (`admin` / `password123`) or click **"Initialize Guest Session"**.
   - Open the **Report Queue** (`#incidents`). Show both the **Messages** and **Conversations** tabs.
   - Press `Ctrl+R` to demonstrate **reload state persistence**—the app stays on the active queue tab without redirecting to Threat Scan.

4. **Minute 4 — Repeat Offender Intelligence:**
   - Navigate to **Repeat Offenders** (`#offenders`).
   - Show how URLs like `http://sbi-kyc-update.xyz` and `sbi-kyc-update.xyz` are normalized into a single entity with cumulative hit counts, peak risk, and timeline entries.

5. **Minute 5 — AI Cyber Safety Assistant & Test Suite:**
   - Open **AI Safety Chat** (`#chat`).
   - Switch to **Victim Mode** and submit a blackmail inquiry. Highlight the warm empathetic opening sentence, the clear key takeaway (*"Do not pay"*), the actionable numbered steps, and verified helplines (**1930, StopNCII.org, 112**).
   - Switch to **Analyst Mode** to demonstrate technical IOC extraction.
   - Switch to the terminal and execute `pytest -q`: demonstrate that all **118 automated tests pass**.
