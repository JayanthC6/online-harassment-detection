# ShieldAI — Online Harassment Detection System

An advanced forensic trust & safety console designed for moderators to review digital safety incidents. 

## Current Stage & What Has Been Built

The project has evolved into a fully functional, enterprise-grade forensic dashboard for trust and safety teams. We have recently completed several major milestones:

### 1. Neurosymbolic Fusion Architecture
- **Dual Engine System**: Fuses a Fine-tuned DistilBERT transformer model (neural) with an explicit Heuristic Rule Engine (symbolic).
- **Noisy-OR Fusion Logic**: Probabilities are combined using a noisy-OR formula, ensuring that strong signals from either the neural or symbolic engine can escalate an incident's severity.
- **Explainability**: Word-level contribution highlighting ensures moderators understand exactly *why* a decision was made.

### 2. External Threat Intelligence Integration
- **Google Safe Browsing**: Extracts URLs from text and checks them against Google's malware and phishing databases.
- **Domain Age Analysis**: Uses WHOIS lookups to identify domains registered in the last 30 days (strong phishing signal).
- **Typosquatting Detection**: Uses Levenshtein distance algorithms to detect domains impersonating high-value targets (e.g., `paypa1.com` instead of `paypal.com`).
- **Data Breach Lookup**: Checks extracted email addresses against Have I Been Pwned (HIBP) to flag known compromised accounts.
- **Graceful Degradation**: External API calls are wrapped in strict async timeouts to prevent the core analysis pipeline from blocking if an external service is down.

### 3. Forensic UI Redesign (React/Vite)
- **Dark Mode "Ink" Aesthetic**: Completely rebuilt the UI to resemble a forensic case-file system rather than a generic SaaS dashboard. Features strict hard edges (no rounded corners), a curated color palette (Ink, Panel, Manila, Redaction Red), and custom Recharts styling.
- **Incident Intelligence Panel**: A dedicated flyout panel for moderators to review extracted Threat Intelligence, explainability highlights, and victim guidance.

### 4. Robust Backend Infrastructure (Python/Flask/MongoDB)
- **Persistent Storage**: Fully functional MongoDB Atlas integration with proper TLS configuration (`certifi`) to prevent silent fallbacks to in-memory storage.
- **Modular Services**: Business logic, ML pipelines, and API routes are strictly segregated for maintainability.

### 5. Real-Time Protection (Chrome Extension)
- **Manifest V3 Architecture**: A lightweight, sideloaded Chrome extension that serves as a real-time client for the ShieldAI backend.
- **Privacy-First Scanning**: Uses `IntersectionObserver` to only scan messages actively visible in the viewport (supported on Gmail and WhatsApp Web). No history is stored.
- **Inline Threat Badges**: Injects non-intrusive, color-coded badges (`⚠ [THREAT]` for high-confidence threats, `✓ SAFE` for benign messages) directly into the DOM next to the text.
- **Deduplication & Truncation**: Smartly skips previously checked messages to save API calls, and automatically truncates massive emails to 1,950 characters to comply with the backend's 2,000 character limit without throwing 400 Bad Request errors.
- **Lightweight Auth**: Secures the connection to the backend using an `X-Extension-Api-Key` header, configurable directly in the extension's popup UI.

## Next Steps
The project is currently in a highly functional state, ready for further refinement in scalability, multilingual support, and deployment automation.
