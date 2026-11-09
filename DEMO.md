# ShieldAI — 5-Minute Evaluation & Viva Demo Script

This script provides an exact, minute-by-minute walkthrough to demonstrate ShieldAI's capabilities to examiners, reviewers, or evaluators.

---

## ⏱️ Pre-Demo Setup (Do this before the presentation)

1. **Terminal 1 (Root Directory):**
   ```powershell
   # Activate virtual environment
   .\venv\Scripts\Activate.ps1
   $env:PYTHONPATH="backend"

   # Seed realistic demo data into SQLite
   .\venv\Scripts\python.exe scripts/seed_demo_data.py --force

   # Launch both Backend (port 5000) and Frontend (port 5173)
   .\start.ps1
   ```
2. **Chrome Browser:**
   - Open Tab 1: [http://localhost:5173](http://localhost:5173) (ShieldAI SOC Dashboard)
   - Open Tab 2: [http://localhost:5173/test.html](http://localhost:5173/test.html) (or `extension/test.html`)
   - Ensure the ShieldAI Chrome extension is loaded in Developer Mode with **"Allow access to file URLs"** toggled ON.

---

## 🕒 Minute 0:00 – 0:45 | Platform Architecture & Operations Center

**What to Say:**
> *"ShieldAI is a neurosymbolic cyber threat intelligence and harassment detection platform designed for digital safety operations. It combines fine-tuned DistilBERT transformer embeddings with deterministic threat intelligence, PII redaction, and an AI crisis assistant with grounded offline fallbacks."*

**What to Show on Screen:**
1. Navigate to **Security Operations Center** (`http://localhost:5173`).
2. Point out:
   - **System Status Pill (top right):** Highlights `Hybrid Mode Active` & `Neural DistilBERT Loaded`.
   - **KPI Cards:** Total Incidents (37+), High Risk Incidents, Average Risk Score.
   - **Recharts Visualizations:**
     - Left: **Flagged Incidents by Threat Category** (BarChart showing distribution across Sextortion, Threat, Phishing, Scam).
     - Right: **30-Day Threat Trend Activity** (AreaChart showing chronological incident spikes).

---

## 🕒 Minute 0:45 – 2:00 | Live Multi-Modal Threat Hunt & Adversarial Normalization

**What to Say:**
> *"Now we will test the neurosymbolic detection engine against three distinct threat vectors: financial phishing with brand spoofing, webcam sextortion with crypto demands, and multilingual Hinglish threats."*

**What to Click:**
- Click **"Threat Hunt & Scan"** on the left sidebar navigation.

### Test Case 1: Brand Impersonation & Phishing SMS
- **Paste into Text Box:**
  ```text
  SBI Alert: Dear customer, your YONO account has been suspended due to pending KYC. Click http://sbi-kyc-update.top to update your PAN immediately or your account will be blocked permanently.
  ```
- **Click:** **"Analyze Message"**
- **Explain Output:**
  - **Risk Score:** `96/100` (High/Critical Risk).
  - **Primary Category:** `Phishing`.
  - **Forensic Signals:** Look-alike brand impersonation (*State Bank of India*), artificial urgency countdown (*suspended/blocked immediately*), low-reputation TLD (*.top*).

### Test Case 2: Digital Extortion & Cryptocurrency Demand
- **Paste into Text Box:**
  ```text
  I have recorded intimate video from your webcam. Send 0.15 BTC ($5,000 USD) to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa within 24 hours or I will leak this video to all your Facebook contacts.
  ```
- **Click:** **"Analyze Message"**
- **Explain Output:**
  - **Risk Score:** `100/100` (Critical Severity Tier).
  - **Primary Category:** `Sextortion`.
  - **Forensic Signals:** Cryptocurrency payment coercion, 24-hour urgency countdown, contact harvesting blackmail bluff.

### Test Case 3: Adversarial Hinglish Intimidation & Doxxing
- **Paste into Text Box:**
  ```text
  tere ghar aake marunga kutte, tu bach ke dikha. I know where you live and your phone number is +919812345678.
  ```
- **Click:** **"Analyze Message"**
- **Explain Output:**
  - **Risk Score:** `98/100` (Critical).
  - **Primary Category:** `Threat`.
  - **Forensic Signals:** Roman-script Hindi threat pattern (`tere ghar aake marunga`), physical stalking/doxxing indicator.
  - **PII Redaction:** Notice phone number is preserved in evidence as `[PHONE REDACTED]`.

### Test Case 4: Benign Banter (Zero False-Positive Proof)
- **Paste into Text Box:**
  ```text
  haha you loser, you beat me again! that was so stupid of me, I forgot my keys.
  ```
- **Click:** **"Analyze Message"**
- **Explain Output:**
  - **Risk Score:** `< 15/100` (Low / Safe).
  - **Status:** Unflagged. Demonstrates our benign insult and self-deprecation dampener.

---

## 🕒 Minute 2:00 – 3:00 | Incident Triage Queue & Repeat Offender Profiling

**What to Say:**
> *"When incidents are detected across platforms or browser extensions, they flow into our centralized, privacy-preserving incident management queue."*

**What to Click:**
1. Click **"Report Queue"** on the left sidebar:
   - **Search Box:** Type `sbi` $\to$ instant client-side filter isolates the phishing report.
   - **Severity Filter:** Select **Critical** $\to$ displays sextortion and threat cases.
   - **Status Filter:** Filter by `open` vs. `reviewing`.
2. Click on the top **Sextortion** incident to expand the **Forensic Detail View**:
   - Show sanitized evidence quote with masked PII.
   - Show legal provisions (*Section 66E / 67 IT Act, Section 384 IPC / Section 308(2) BNS*).
   - Change Status from `open` to `reviewing` $\to$ updates database and logs an audit event.
3. Click **"Repeat Offenders"** tab:
   - Highlight **`anon_blackmailer_42`**: 5 hits, 100% peak risk, categorized under *Sextortion*.
   - Highlight **`sbi-kyc-update.top`**: 6 hits, flagged domain.
   - Highlight **`+919876543210`**: 4 hits, banned phone actor.
   - Click to reveal the chronological activity timeline.

---

## 🕒 Minute 3:00 – 4:00 | AI Crisis Assistant (Victim vs. Analyst Persona)

**What to Say:**
> *"ShieldAI provides a dual-persona AI crisis counselor. It features built-in prompt-injection resilience, emergency helpline escalation, and a deterministic offline fallback when an external LLM API is unavailable."*

**What to Click:**
- Click **"AI Assistant"** on the left sidebar.

### Test 1: Victim Support Mode (Empathetic & Concrete)
- **Select Persona:** `Victim Support Mode`
- **Type Message:**
  ```text
  Someone is blackmailing me on Instagram saying they have photos of me and demanding $500 in 24 hours. I'm terrified.
  ```
- **Send & Observe:**
  - Notice the **Engine Badge** (`engine: claude` or `engine: rules`).
  - Tone is calm, supportive, and never blames the victim.
  - Specifically addresses the amount (`$500`), platform (`Instagram`), and deadline (`24 hours`).
  - Mentions that many such claims are mass-sent bluffs.
  - Directs the victim to **National Cybercrime Helpline 1930** and **cybercrime.gov.in**.

### Test 2: Security Analyst Mode (Forensic Intelligence)
- **Select Persona:** `Security Analyst Mode`
- **Type Message:**
  ```text
  URGENT: Your SBI net banking has been suspended. Update your PAN at http://sbi-kyc-update.top or call +919876543210
  ```
- **Send & Observe:**
  - Structured output with **Assessed Risk Level**, **Extracted Indicators**, **Observed Attacker Tactics**, and statutory legal provisions under the **IT Act 2000 & BNS/IPC**.

---

## 🕒 Minute 4:00 – 5:00 | Real-Time Chrome Extension (Manifest V3)

**What to Say:**
> *"Finally, we demonstrate ShieldAI's Manifest V3 browser extension performing non-intrusive, real-time scanning on live web pages."*

**What to Show on Screen:**
1. Switch to the browser tab with [http://localhost:5173/test.html](http://localhost:5173/test.html) (or `extension/test.html`).
2. Point out:
   - Red **[Critical Threat]** badges injected next to physical threats.
   - Orange **[Phishing Alert]** badges injected next to the fake bank message.
   - Clean posts have **no badges** by default (safe badge suppression active to eliminate clutter).
3. Click the **ShieldAI extension icon** in the Chrome toolbar:
   - Toggle **"Show Safe Badges"** ON $\to$ refresh $\to$ clean posts now show green **[Safe]** badges.
   - Toggle **"Scan this website"** OFF $\to$ demonstrates instant per-site opt-out.
4. Open [http://localhost:5173/test_generic.html](http://localhost:5173/test_generic.html):
   - Demonstrates the **Generic Fallback Scanner** working on ordinary `<p>` paragraph text blocks without special CSS classes or selectors.

---

## 🏁 Concluding Statement
> *"In summary, ShieldAI bridges the gap between machine learning classification and real-world cyber safety operations. It provides robust adversarial normalization, multi-threat intelligence, privacy-first incident triaging, and real-time client protection."*

