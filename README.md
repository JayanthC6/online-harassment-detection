# ShieldAI — Online Harassment Detection & Forensic Dashboard

ShieldAI is an advanced, multi-modal forensic trust & safety platform designed to assist moderators and digital safety teams in identifying, classifying, and mitigating digital abuse. 

It provides real-time protection through a Chrome extension and deep forensic capabilities through a dedicated moderator dashboard.

## 🌟 Core Features

### 1. Neurosymbolic Intelligence Pipeline
ShieldAI employs a dual-engine architecture to ensure both high recall and interpretable decision-making:
- **Neural Engine**: Uses a fine-tuned DistilBERT transformer model for deep contextual understanding of text, identifying nuanced intent (e.g., subtle threats or implicit harassment).
- **Symbolic Engine**: A deterministic heuristic ruleset for explicit keyword matching, ensuring immediate flagging of known slurs and obvious malicious patterns.
- **Noisy-OR Fusion**: Probabilities from both engines are mathematically fused using Noisy-OR logic, ensuring strong signals from either source correctly escalate the overall risk score.
- **Transformer Explainability**: Features token-level attribution (via Captum) to highlight exactly which words contributed most heavily to a neural classification.

### 2. External Threat Intelligence Integration
To defend against multi-vector attacks, ShieldAI integrates external OSINT/Threat Intel lookups:
- **Google Safe Browsing**: Extracts URLs and checks them against malware and phishing blocklists.
- **Typosquatting Detection**: Uses Levenshtein distance algorithms to detect domains impersonating high-value targets (e.g., `paypa1.com` instead of `paypal.com`).
- **Domain Age Analysis**: Uses WHOIS lookups to identify domains registered in the last 30 days, which is a strong phishing indicator.
- **Data Breach Lookup (HIBP)**: Checks extracted email addresses against known data breaches to flag potentially compromised accounts.
- **Resilient Fallbacks**: All external API calls are wrapped in strict async timeouts to prevent the core analysis pipeline from blocking if an external service goes down.

### 3. Forensic UI Dashboard (React/Vite)
A comprehensive, specialized interface designed for trust & safety teams:
- **Dark Mode "Ink" Aesthetic**: Built to resemble a forensic case-file system with a curated color palette (Ink, Panel, Manila, Redaction Red) and sharp geometric edges.
- **Incident Intelligence Panel**: A dedicated flyout panel for reviewing detailed incident data, explainability highlights, and victim guidance.
- **Moderator Queues**: Dedicated views for isolated messages, full conversational contexts, and user-submitted complaints.
- **Behavioral Intelligence**: Groups cross-platform incidents by actor, computing aggregate escalation scores to identify chronic offenders.

### 4. Real-Time Protection (Chrome Extension)
- **Manifest V3 Architecture**: A lightweight Chrome extension serving as a real-time client for the ShieldAI backend.
- **Privacy-First Scanning**: Uses `IntersectionObserver` to only scan messages actively visible in the viewport (supported on Gmail and WhatsApp Web). No browsing history is stored.
- **Inline Threat Badges**: Injects non-intrusive, color-coded badges directly into the DOM to alert users of potential threats.
- **Secure Authentication**: Secures backend communication using an `X-Extension-Api-Key` header, easily configurable in the extension's popup.

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.10+, Flask, PyTorch, HuggingFace Transformers, Captum, MongoDB Atlas.
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Lucide Icons.
- **Extension**: Vanilla JavaScript, Chrome Extension API (Manifest V3).

---

## 🚀 Setup & Installation

### 1. Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in the required keys:
   - `MONGO_URI`: Your MongoDB Atlas connection string (use `certifi` if required).
   - `JWT_SECRET_KEY`: A secure random string for JWT signing.
   - `GOOGLE_SAFE_BROWSING_KEY`: (Optional) For URL threat intel.
   - `HF_TOKEN`: (Optional) For transformer explainability (Captum).
   - `EXTENSION_API_KEY`: A secure key used by the Chrome extension to authenticate with the backend.

5. **Start the Flask server:**
   ```bash
   python app.py
   ```
   The backend will run on `http://localhost:5000`.

### 2. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The dashboard will run on `http://localhost:5173`. Navigate to `/admin` to log in.

### 3. Chrome Extension Setup

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in the top right corner).
3. Click **Load unpacked** and select the `extension` folder in this repository.
4. Click the ShieldAI icon in your Chrome toolbar and enter the `EXTENSION_API_KEY` you defined in your backend `.env` file to authenticate.
5. The extension is now active on supported sites (e.g., WhatsApp Web).

---

## 🔒 Security & Privacy

ShieldAI is designed with strict privacy constraints:
- **No Long-Term Extension Storage**: The Chrome extension does not locally store or log your private messages. It only processes what is currently visible in your browser viewport.
- **Stateless Analysis Option**: The API supports stateless predictions that generate trust & safety metrics without persisting PII to the database.
- **Role-Based Access Control**: The forensic dashboard utilizes strict JWT-based RBAC (`Admin`, `Moderator`, `Viewer`) to ensure only authorized personnel can review incidents and take mutating actions (e.g., banning actors).

---

## 🛠️ Contributing
We welcome contributions to expand threat intelligence feeds, improve model recall, or add integrations for new social platforms. Please submit issues and pull requests to the repository.
