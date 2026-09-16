# ShieldAI — Cyber Threat Intelligence & Harassment Detection Platform

> **A production-grade, multi-modal cyber safety platform** for detecting online harassment, phishing, scams, threats, and social engineering attacks. Built for trust & safety teams, digital forensic investigators, and end-users reporting cyber incidents.

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Architecture & Pipeline](#architecture--pipeline)
3. [Core Features & Capabilities](#core-features--capabilities)
4. [Tech Stack](#tech-stack)
5. [Setup & Installation](#setup--installation)
6. [Environment Variables](#environment-variables)
7. [Running the Application](#running-the-application)
8. [Role-Based Access Control](#role-based-access-control)
9. [Project Structure](#project-structure)

---

## Overview

ShieldAI is a full-stack forensic trust & safety platform that leverages neurosymbolic AI (a fusion of Deep Learning and determinisitic rulesets) alongside external threat intelligence feeds to classify, score, and explain digital abuse incidents. 

The platform serves two primary audiences:
- **End User / Victim:** Uses the **Threat Hunt** console to analyze individual messages, conversations, screenshots, audio, and documents for threats.
- **Admin / Moderator:** Uses the **Cyber SOC Dashboard** to review incident queues, manage behavioral profiles of threat actors, and analyze platform-wide trends.

---

## Architecture & Pipeline

ShieldAI utilizes a sophisticated **Neurosymbolic Intelligence Pipeline** designed to maximize both recall and explainability.

### The Prediction Pipeline
1. **Input Parsing & Extraction:** Text is extracted from the user's modality of choice (text, audio, image, PDF, or conversation logs).
2. **Multilingual Translation (NLLB):** Non-English text is detected and automatically translated to English using the `facebook/nllb-200-distilled-600M` transformer model to ensure global threat detection.
3. **PII Masking:** Personally Identifiable Information (emails, phone numbers) is stripped out to protect victim privacy.
4. **Primary Neural Engine:** A fine-tuned `distilbert-base-uncased` transformer analyzes the semantic context of the text.
5. **Heuristic Multi-Label Engine:** A deterministic ruleset (`heuristic.py`) scans for specific structural threats that neural models often struggle with (e.g., grammatical extortion, job scams, investment fraud).
6. **External Threat Intel:** Asynchronous API lookups against Google Safe Browsing, WHOIS (domain age), and HIBP (breach data) enrich the context.
7. **Noisy-OR Fusion:** The neural confidence and heuristic signals are fused using Noisy-OR logic to calculate a final, highly accurate **Risk Score (0-100)**.
8. **Evidence Generation:** The system assigns a severity tier and outputs a tailored Forensic Evidence Playbook for the victim.

---

## Core Features & Capabilities

### 1. Multi-Modal Analysis
ShieldAI supports analyzing threats across almost any medium:
- **Plain text:** Direct message or paragraph input.
- **Conversation files:** Native parsing of exported WhatsApp (`.txt`) and Instagram (`.json`) chat logs.
- **Screenshots / Images:** Optical Character Recognition (OCR) via `EasyOCR` + `OpenCV`.
- **Audio / Video:** Local speech-to-text transcription via `OpenAI Whisper`.
- **Documents:** Full PDF parsing and text extraction via `pdfplumber`.

### 2. Forensic Dashboard (SOC Interface)
A full Cyber Security Operations Center interface for moderators:
- **Trend Analytics:** Z-score based anomaly highlighting for daily report volumes and category distribution.
- **Moderator Queue:** Paginated, searchable tables for individual messages and full conversation replays.
- **Incident Intelligence Panel:** Deep-dive into an incident to see fusion evidence, token heatmaps (via Captum Integrated Gradients), threat intel findings, and typosquatting alerts.
- **Behavioral Profiling:** Tracks repeat offenders across multiple incidents, upgrading their threat level based on escalating behavior over a chronological timeline.

### 3. AI-Powered Chatbot (Dual Persona)
An embedded conversational AI assistant powered by **Groq (`llama-3.1-8b-instant`)**:
- **Victim Persona:** Empathetic guidance on reporting, safety steps, and legal options.
- **Analyst Persona:** Tactical investigation support based on fusion evidence and behavioral profiles.
- **Context-Aware:** The chatbot inherently understands the active prediction result and restricts itself from answering off-topic queries.

### 4. Real-Time Chrome Extension
A lightweight Manifest V3 Chrome extension providing real-time threat scanning in the browser:
- **Viewport-Only Scanning:** Uses `IntersectionObserver` to scan only messages currently visible on screen (e.g., WhatsApp Web). No mass-scanning or history storage.
- **Inline Badges:** Injects color-coded risk badges directly into the DOM next to dangerous messages.

### 5. Incident Complaint System
- **Structured Submissions:** Users can file formal complaints through a dedicated public portal.
- **AI Summarization:** Generates structured incident summaries automatically via Groq.
- **Deduplication:** Uses `sentence-transformers` to detect semantically similar reports and prevent queue spam.

---

## Tech Stack

**Backend (Python/Flask)**
- **Framework:** Flask, Flask-CORS, Flask-Limiter
- **AI & ML:** PyTorch, Transformers (HuggingFace), Captum (Explainability), Scikit-Learn, NLTK, Sentence-Transformers, OpenAI-Whisper, EasyOCR
- **External APIs:** Groq, Google Safe Browsing, HIBP
- **Data & Parsing:** Pandas, pdfplumber, python-whois
- **Database:** MongoDB (PyMongo)

**Frontend (React/Vite)**
- **Framework:** React 18, Vite
- **Styling:** TailwindCSS, Framer Motion (Animations), Lucide React (Icons)
- **Routing:** React Router DOM
- **Charts:** Recharts

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (Local or Atlas)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/JayanthC6/online-harassment-detection.git
cd online-harassment-detection
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```
*(Note: Upon first run, the backend will download necessary ML models including DistilBERT, Whisper, NLLB-200, and EasyOCR models. This may take several minutes and requires an internet connection.)*

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Required for Chatbot and Summarization
GROQ_API_KEY=your_groq_api_key_here

# Required for Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key

# Required for Threat Intelligence
GOOGLE_SAFE_BROWSING_API_KEY=your_google_api_key
HIBP_API_KEY=your_have_i_been_pwned_key

# Database (Optional - defaults to in-memory if omitted)
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/shieldai?retryWrites=true&w=majority
```

---

## Running the Application

To run the application locally, you need to start both the backend server and the frontend Vite server.

**1. Start the Flask Backend:**
```bash
# From the root directory, activate the venv and run:
cd backend
python app.py
```
*The backend will run on `http://127.0.0.1:5000`.*

**2. Start the React Frontend:**
```bash
# In a new terminal window:
cd frontend
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

---

## Role-Based Access Control

ShieldAI implements strict RBAC to separate victim portals from administrative tools.

- **Admin Account:** `admin@shieldai.internal` / `Admin@123`
- **Standard Account:** `analyst@shieldai.internal` / `Analyst@123`

*End users can access the public Threat Hunt and Complaint Submission tools without an account.*

---

## Project Structure

```
online-harassment-detection/
├── backend/
│   ├── api/                   # Flask Blueprints and routes
│   ├── config/                # Evidence playbooks and static config
│   ├── ml/                    # Machine Learning pipeline
│   │   ├── adapters/          # DistilBERT, Heuristic, ThreatIntel, Multilingual
│   │   ├── models/            # Stored model weights (if trained locally)
│   │   └── chatbot.py         # Groq LLM logic
│   ├── services/              # Business logic (Evidence, Prediction, DB)
│   ├── app.py                 # Flask application entry point
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React UI components
│   │   ├── pages/             # Route views (Dashboard, ThreatHunt, etc.)
│   │   └── App.jsx            # React application entry point
│   └── vite.config.js
└── extension/                 # Chrome Manifest V3 extension
```
