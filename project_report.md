# ShieldAI: A Multi-Modal Neurosymbolic Platform for Online Harassment Detection, Cyber Threat Intelligence, and Forensic Evidence Triaging

**Academic Project Report & Technical Specification**  
*Degree: Master of Computer Applications (MCA)*  
*Domain: Cyber Safety, Natural Language Processing, Threat Intelligence, Web Security*

---

## Executive Summary

The proliferation of digital communication platforms has been accompanied by a surge in online toxicity, cyberbullying, targeted harassment, financial fraud, and digital extortion (e.g., webcam sextortion and loan app harassment). Traditional automated moderation systems exhibit critical vulnerabilities:
1. **Model Blindness to Obfuscation:** Transformer models trained on standard corpora are routinely bypassed by leetspeak, symbol substitutions, unicode zero-width insertions, and spaced-out characters.
2. **Narrow Classification Scope:** Standard toxic comment classifiers classify generalized toxicity or obscenity but fail to detect structured financial phishing, crypto scams, or extortion tactics with urgency deadlines and payment addresses.
3. **Conversational Attribution Failures:** Multi-party conversation analysis frequently flags victims defending themselves or bystanders attempting to assist, rather than isolating the perpetrator.
4. **Lack of Forensic Preservation & Triaging Workflow:** Automated systems rarely bridge detection with actionable evidence preservation, repeat offender tracking, and victim-support guidance aligned with legal frameworks (such as India's Information Technology Act, 2000 and the Bharatiya Nyaya Sanhita, 2023).

**ShieldAI** resolves these challenges by introducing an end-to-end **neurosymbolic cyber safety system**. ShieldAI unifies a fine-tuned DistilBERT transformer with an adversarial text normalization pipeline, a deterministic heuristics and threat intelligence correlation engine, a high-throughput Chrome browser extension (Manifest V3), a React-based Security Operations Center (SOC) dashboard, and an AI safety assistant powered by Groq (default `llama-3.3-70b-versatile`) and Claude (`claude-haiku-5-5`) with grounded offline fallback rules.

---

## 1. Introduction & Problem Statement

### 1.1 The Cyber Threat Landscape
Digital communication channels—including social networks (X, Instagram), instant messaging platforms (WhatsApp, Telegram), and web forums—have become vectors for malicious digital behavior:
- **Severe Cyberbullying & Doxxing:** Systematic intimidation, release of personal contact details, and incitement to self-harm.
- **Digital Extortion & Sextortion:** Intimidation schemes threatening the distribution of private images or fabricated recordings unless cryptocurrency ransoms are transferred within strict deadlines.
- **Urgent Financial Phishing:** Brand impersonation (e.g., State Bank of India, major telecom providers) threatening immediate account suspension to harvest banking credentials.
- **Hinglish & Roman-Script Abuse:** Code-mixed abusive threats commonly used in South Asian online interactions that evade standard English-centric toxic comment models.

### 1.2 Limitations of Existing Approaches
Current commercial and open-source solutions exhibit three primary architectural deficiencies:
1. **Purely Neural Systems (Over-Reliance on Probabilities):** Deep neural networks produce uncalibrated probabilities that fluctuate on trivial morphological shifts (e.g., `k!ll` vs. `kill`). Furthermore, neural models cannot reliably extract structured forensic indicators (such as punycode domains or cryptocurrency wallet addresses).
2. **Purely Heuristic Systems (Fragile Regex Rules):** Regular expressions cannot comprehend nuanced semantic insults, sarcastic attacks, or conversational context, resulting in high false-positive rates on benign banter.
3. **Absence of Actionable Victim Triaging:** Standard moderation tools terminate at binary flagging or content removal. Victims are left without structured evidence dossiers, repeat offender tracking, or clear statutory legal paths (e.g., Sections 66D, 66E, 67, 67A of the Information Technology Act, 2000 alongside Sections 308(2), 351(2), 78, 79 of the Bharatiya Nyaya Sanhita, 2023 / Sections 384, 506, 354D, 509 IPC).

### 1.3 Project Objectives
ShieldAI was engineered to achieve four core objectives:
1. **Adversarial Resilience:** Maintain robust detection accuracy against leetspeak, zero-width characters, repeated letters, and mixed spacing across both English and romanized Hindi (Hinglish).
2. **Hybrid Neurosymbolic Architecture:** Fuse DistilBERT neural embeddings with deterministic threat intel (brand matching, punycode, crypto payment keywords, and urgency signals) calibrated onto a 0–100 operational risk scale.
3. **Real-Time Client-Side Protection:** Provide a low-overhead, privacy-respecting Chrome extension that scans social feeds and generic web pages asynchronously with batch throttling.
4. **Forensic Evidence & Incident Operations:** Equip Trust & Safety analysts and citizens with an interactive triage dashboard, repeat offender correlation, automated PII sanitization, and a dual-persona AI crisis counselor.

---

## 2. System Architecture & Methodology

### 2.1 Architectural Overview
ShieldAI operates across four decoupled layers:
```
+--------------------------------------------------------------------------+
|                        Client & Ingestion Layer                          |
|  - Chrome Extension (Manifest V3, DOM Observer, Batch Throttler)         |
|  - React 18 + Vite Operations Center (Recharts, Incident Triage Queue)   |
|  - Multi-Format Evidence Parsers (WhatsApp TXT, Telegram JSON, PDF, TXT) |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
|                     API Gateway & Security Layer                         |
|  - Flask RESTful API (Port 5000, backend/app.py)                         |
|  - JWT Authentication, Role Guards, Rate Limiting (120 req/min)          |
|  - Automated PII Redaction Engine (Phone, Email, Aadhaar, PAN)           |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
|                  Neurosymbolic Detection Engine                          |
|  - Adversarial Normalizer (backend/services/model_service.py)            |
|  - DistilBERT Multi-Label Transformer (Fine-tuned weights)               |
|  - Heuristics & Threat Intel (backend/ml/adapters/threat_intel.py)       |
|  - Operational Multi-Label Calibrator (Piecewise 0-100 score mapping)    |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
|                 Persistence & Crisis Support Layer                       |
|  - Persistent SQLite / SQLAlchemy Database (backend/core/database.py)    |
|  - Relational Repeat Offender Entity Index (backend/services/offender_service.py) |
|  - Multi-Provider LLM Chatbot (Groq Llama 3.3 / Claude Haiku / Rules)   |
|  - Grounded Offline Knowledge Base & Interception Guardrails             |
|  - Statutory Legal Playbook (IT Act 2000 & BNS 2023 / IPC 1860)          |
+--------------------------------------------------------------------------+
```

### 2.2 Adversarial Text Normalization Pipeline
*Implementation: `ModelService._normalize_text()` in `backend/services/model_service.py`*

Before evaluation by the neural model or heuristics rules, all incoming text passes through a multi-stage normalization filter:
1. **Zero-Width Character Stripping:** Eliminates `\u200B` (zero-width space), `\u200C` (ZWNJ), `\u200D` (ZWJ), and `\uFEFF` (BOM) inserted to break keyword boundaries.
2. **Leetspeak & Symbol De-obfuscation:** Dynamically normalizes canonical digit/symbol substitutions:
   $$\{1, !, |\} \to \text{'i'} \quad|\quad \{0\} \to \text{'o'} \quad|\quad \{3\} \to \text{'e'} \quad|\quad \{@, 4\} \to \text{'a'} \quad|\quad \{5, \$\} \to \text{'s'}$$
   Handles masked profanity tokens like `f*ck`, `f**k`, `b!tch`, `k1ll`.
3. **Repeated Character Compression:** Collapses multi-character elongations (`kiiiillllll` $\to$ `kill`, `stuuuupid` $\to$ `stupid`) while preserving valid double consonants (e.g., `kill`, `kiss`, `feed`).
4. **Mixed Spacing Consolidation:** Detects and merges spaced-out letters used to evade tokenizers (`k i l l` $\to$ `kill`, `d i e` $\to$ `die`).

### 2.3 Neurosymbolic Detection Engine
The detection engine synthesizes three parallel evaluation paths:
- **Neural Transformer (DistilBERT):** Evaluates multi-label semantic toxicity across 6 trained categories: *Hate Speech*, *Cyberbullying / Harassment*, *Physical Threat*, *Toxicity / Offensive Language*, *Profanity*, and *Clean*. Calibrated decision thresholds isolate high-confidence alerts (`Threat` = 0.5332, `Hate Speech` = 0.8076, `Cyberbullying / Harassment` = 0.8905, `Toxicity / Offensive Language` = 0.4210, `Profanity` = 0.9966, `Clean` = 0.6906).
- **Threat Intelligence & Brand Impersonation:**
  - Extracts and correlates domain names, IP addresses, punycode characters, and suspicious top-level domains (`.top`, `.xyz`, `.click`, `.live`).
  - Computes Levenshtein edit distances against `TARGET_BRANDS` (`paypal.com`, `apple.com`, `google.com`, `microsoft.com`, `amazon.com`, `netflix.com`) and flags domains where edit distance $\le 2$.
  - Identifies look-alike brand spoofing for Indian banking entities (e.g., State Bank of India, HDFC, ICICI, Paytm) and international financial services (`paypa1`, `b1nance`, `amaz0n`).
  - Matches cryptocurrency payment keywords and wallet address formats (`0x` + 40 hex, `bc1` / `1` / `3` Bitcoin, USDT, ETH) via regex heuristics.
  - Extracts artificial urgency deadlines (e.g., `within 24 hours`, `expires today`, `action required`) via pattern matching.

---

## 3. Multi-Provider LLM & Safety Guardrails

### 3.1 LLM Providers (Groq & Anthropic)
ShieldAI integrates a modular multi-provider architecture configured via environment variables:
- `LLM_PROVIDER`: `groq`, `anthropic`, or `none`.
- **Groq Provider:** Connects to Groq's high-speed inference engine using its OpenAI-compatible endpoint (`https://api.groq.com/openai/v1`). Default model is dynamically read from `GROQ_MODEL` (defaulting to `llama-3.3-70b-versatile`, providing 128k context, strong cybersecurity reasoning, and fast inference).
- **Anthropic Provider:** Connects to Anthropic Claude messages API. Default model is dynamically read from `ANTHROPIC_MODEL` (defaulting to `claude-haiku-5-5`).
- **Resilient Fallback:** If the configured provider is missing, encounters rate limiting (HTTP 429), times out after 10 seconds, or provides an invalid key, the system automatically falls back to the deterministic rule engine with a user-facing note (`*Note: AI service unavailable, showing basic guidance.*`), logs the failure reason without ever leaking or printing the API key, and renders the badge as `Rules`.
- **UI Badge:** Transparently indicates the active engine: `Groq`, `Claude`, or `Rules`.

### 3.2 Dual Personas
1. **Victim Mode:**
   - Starts with one warm sentence acknowledging user emotion and distress without false safety guarantees (`you are safe now` is explicitly prohibited).
   - One concise line stating the core takeaway (e.g., *"Do not pay: payment rarely stops demands, and many such messages are bluffs."*).
   - Up to 6 numbered steps (each exactly one single sentence): 1) don't pay or reply, 2) preserve screenshots and payment demands, 3) block account and report on the specific platform (mentioned naturally only once), 4) secure credentials and enable 2FA, 5) report to official portals (helpline 1930 for financial cyber fraud, `cybercrime.gov.in` for formal complaints, `stopncii.org` for non-consensual imagery), 6) seek support from a trusted person.
   - Closing line: *"If you ever feel in immediate danger, call 112."*
2. **Analyst Mode:**
   - Structured SOC triage format: Classification, Assessed Risk Level and Score (strictly grounded in scan data), Deduplicated Indicators, Evidenced Attacker Tactics, Recommended SOC Actions (distinguishing SMS vs Email channels), Uncertainties & Investigation Limits, and Statutory Legal Provisions using probabilistic phrasing (*"may fall under Section 66D/66E IT Act"*).
   - Post-check validation: Enforces that the model response does not contradict the scan score or severity tier; if contradiction occurs, it safely falls back to the rule-based analyst response.

### 3.3 Safety, PII Masking & Interception Guardrails
- **Pre-Model Crisis Interception:** Explicit self-harm or immediate physical danger distress phrases (e.g., *"I want to end my life"*) are intercepted by deterministic rules **before any model call** occurs. It provides emergency numbers (`112`, `14416` Tele-MANAS, `1800-599-0019` KIRAN, `+91 9999 666 555` Vandrevala), contains zero cyber-safety steps, offers no false promises, and concludes with: *"I'm here, and you're welcome to keep talking to me too."*
- **Colloquial Hyperbole Filtering:** Benign idioms (*"this exam is killing me"*, *"die of laughter"*) are protected from false crisis triggering.
- **Untrusted User Delimiter Wrapping:** User-supplied messages are enclosed in `<<<PASTED_USER_CONTENT>>> ... <<</PASTED_USER_CONTENT>>>` and treated strictly as passive data, neutralizing prompt injection attempts.
- **Automated PII Redaction:** Phone numbers, email addresses, Aadhaar numbers, and PAN cards are masked with `[REDACTED_*]` tags prior to transmitting text to external LLM APIs.
- **User Notice:** Chat pages display a prominent privacy notice: *"Replies are generated by an AI model. Do not share personal details."*

---

## 4. Model Evaluation Results & Confusion Matrices

### 4.1 Dataset Partitioning & Methodology
Evaluation was conducted on the held-out test dataset `backend/data/test.csv` (19,258 rows, 7,603 KB, 21,628 total positive class annotations). To eliminate data leakage and ensure scientifically rigorous, unbiased evaluation, the dataset was formally partitioned into two disjoint, stratified halves using a fixed pseudorandom seed (`seed = 42`):
1. **Tuning Set (`backend/data/tune.csv`, 9,629 rows):** Used exclusively to profile rule false-positive rates and calibrate severity caps.
2. **Held-Out Final Evaluation Set (`backend/data/final.csv`, 9,629 rows):** Completely held out and sealed during tuning, and evaluated **strictly once** after all model thresholds and heuristic rules were locked.

Both halves have zero overlapping texts (`overlap == 0`) and preserve identical stratified class balance across all 14 multi-label combinations.

> [!IMPORTANT]
> **Headline Metric: Macro-Averaged F1 Across 5 Abuse Labels**  
> Because the dataset contains 16,000 clean examples (8,000 in each half), Micro-Averaged F1 is heavily dominated by the high true negative rate of clean text (~92.4%). Consequently, **Macro Average F1 over the 5 abuse categories (excluding Clean)** is the headline metric for assessing real threat detection capability.

### 4.2 Active Calibrated Decision Thresholds (`thresholds.json`)
- **Hate Speech:** `0.8076`
- **Cyberbullying / Harassment:** `0.8905`
- **Threat:** `0.5332`
- **Toxicity / Offensive Language:** `0.4210`
- **Profanity:** `0.9966`
- **Clean:** `0.6906`

---

### 4.3 Held-Out Final Benchmark Results (`backend/data/final.csv` — 9,629 rows)
The locked pipeline was evaluated **once** on the untouched `final.csv` held-out set (10,815 positive annotations).

> **Headline Operational Benchmark (5 Abuse Labels, Excluding Clean):**  
> - **DistilBERT Neural Model Alone:** Macro F1 = **0.7449**  
> - **Full Hybrid Engine (Model + Rules):** Macro F1 = **0.7387** ($\Delta\text{F1} = -0.0062$)  
> 
> *Overall Benchmark Across All 6 Taxonomy Labels (Including Clean):*  
> - **DistilBERT Neural Model Alone:** Macro F1 = **0.7826**  
> - **Full Hybrid Engine (Model + Rules):** Macro F1 = **0.7773** ($\Delta\text{F1} = -0.0053$)

#### Evaluation (a): DistilBERT Neural Model Alone (with `thresholds.json`)

| Label | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **Hate Speech** | 0.8853 | 0.7545 | 0.8147 | 440 |
| **Cyberbullying / Harassment** | 0.7572 | 0.7636 | 0.7604 | 588 |
| **Threat** | 0.4444 | 0.6897 | 0.5405 | 29 |
| **Toxicity / Offensive Language** | 0.8322 | 0.7681 | 0.7989 | 1,285 |
| **Profanity** | 0.8186 | 0.8013 | 0.8098 | 473 |
| **Clean** | 0.9613 | 0.9809 | 0.9710 | 8,000 |
| **Macro Average (5 Abuse Labels)** | **0.7475** | **0.7554** | **0.7449** | **2,815** |
| **Macro Average (All 6 Labels)** | **0.7832** | **0.7930** | **0.7826** | **10,815** |
| **Micro Average** | **0.9251** | **0.9259** | **0.9255** | **10,815** |

##### Per-Label 2x2 Confusion Matrices (Format: `[[TN, FP], [FN, TP]]`):
- **Hate Speech:** `[[9146, 43], [108, 332]]`
- **Cyberbullying / Harassment:** `[[8897, 144], [139, 449]]`
- **Threat:** `[[9575, 25], [9, 20]]`
- **Toxicity / Offensive Language:** `[[8145, 199], [298, 987]]`
- **Profanity:** `[[9072, 84], [94, 379]]`
- **Clean:** `[[1313, 316], [153, 7847]]`

---

#### Evaluation (b): Full Hybrid Detection Engine (Model + Rules + Threat Intel)

| Label | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **Hate Speech** | 0.8853 | 0.7545 | 0.8147 | 440 |
| **Cyberbullying / Harassment** | 0.7377 | 0.7653 | 0.7513 | 588 |
| **Threat** | 0.4167 | 0.6897 | 0.5195 | 29 |
| **Toxicity / Offensive Language** | 0.8308 | 0.7681 | 0.7982 | 1,285 |
| **Profanity** | 0.8141 | 0.8055 | 0.8098 | 473 |
| **Clean** | 0.9601 | 0.9806 | 0.9703 | 8,000 |
| **Macro Average (5 Abuse Labels)** | **0.7369** | **0.7566** | **0.7387** | **2,815** |
| **Macro Average (All 6 Labels)** | **0.7741** | **0.7940** | **0.7773** | **10,815** |
| **Micro Average** | **0.9222** | **0.9260** | **0.9241** | **10,815** |

##### Per-Label 2x2 Confusion Matrices (Format: `[[TN, FP], [FN, TP]]`):
- **Hate Speech:** `[[9146, 43], [108, 332]]`
- **Cyberbullying / Harassment:** `[[8881, 160], [138, 450]]`
- **Threat:** `[[9572, 28], [9, 20]]`
- **Toxicity / Offensive Language:** `[[8143, 201], [298, 987]]`
- **Profanity:** `[[9069, 87], [92, 381]]`
- **Clean:** `[[1303, 326], [155, 7845]]`

---

### 4.4 Final Comparison: Model Alone vs. Full Hybrid Engine ($\Delta$F1)

| Label | Model F1 | Hybrid F1 | Delta ($\Delta$F1) | Operational Analysis & Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **Hate Speech** | 0.8147 | 0.8147 | `0.0000` | Identical; high neural precision maintained without rule degradation |
| **Cyberbullying / Harassment** | 0.7604 | 0.7513 | `-0.0091` | Hybrid rules add sextortion and Hinglish coverage with minimal precision impact |
| **Threat** | 0.5405 | 0.5195 | `-0.0211` | Physical harm rules trigger 3 safety alerts on severe phrases not labelled as threats in dataset (0 new TPs, 3 FPs) |
| **Toxicity / Offensive Language** | 0.7989 | 0.7982 | `-0.0006` | Virtual parity ($0.7982$ vs $0.7989$); neural model handles nuanced English insults |
| **Profanity** | 0.8098 | 0.8098 | `-0.0001` | Identical performance; dictionary verification suppresses false profanity signals |
| **Clean** | 0.9710 | 0.9703 | `-0.0007` | High conversational dialogue retention ($97.0\%$ F1) |
| **Headline: 5-Abuse Macro** | **0.7449** | **0.7387** | **-0.0062** | **Full hybrid engine achieves 0.7387 F1 vs 0.7449 for model alone (-0.0062 Delta)** |
| **Overall: 6-Label Macro** | **0.7826** | **0.7773** | **-0.0053** | **Full hybrid engine achieves 0.7773 F1 vs 0.7826 for model alone (-0.0053 Delta)** |
| **Micro Average** | **0.9255** | **0.9241** | **-0.0014** | Micro F1 is 0.9241 calculated over all 10,815 label annotations in the held-out test split |

---

### 4.5 Independent Evaluation of Fraud & Financial Scam Rules

#### (a) UCI SMS Spam Collection Benchmark
The engine's fraud and phishing layer was evaluated against the **UCI SMS Spam Collection** (5,572 real-world SMS messages). To maintain methodological rigor, the dataset was split 50/50 with a fixed seed (42) into a tuning set (`sms_tune.tsv` — 2,786 rows: 2,412 ham, 374 spam) and an untouched held-out final set (`sms_final.tsv` — 2,786 rows: 2,413 ham, 373 spam).

**Error Profiling on Tuning Split (`sms_tune.tsv`):**
A random sample of 100 false negatives on `sms_tune.tsv` (seed 42) was categorized into operational types:
- **Premium-rate subscription marketing:** 57 (57%) — ringtone subscriptions, dating chatlines, football updates (e.g., *"Txt CHAT to 86688 now!"*, *"FREE RINGTONE text FIRST to 87131 for a poly"*).
- **Prize/lottery scam:** 23 (23%) — UK 2000s prize and award notifications (e.g., *"WINNER!! As a valued network customer you have been selected to receive a £900 prize reward!"*).
- **Phishing/credential lures:** 6 (6%) — deceptive account verification links.
- **Other:** 14 (14%) — adult dating invitations and miscellaneous commercial offers.

**Held-Out Benchmark on `sms_final.tsv` (Evaluated Once):**
The locked engine was evaluated on `sms_final.tsv` using the flagged threshold ($\ge 50.0$ on Scam / Phishing):

| Metric | Measured Value | Operational Interpretation |
| :--- | :--- | :--- |
| **Total Evaluated Messages** | **2,786** | 2,413 ham (86.6%), 373 spam (13.4%) |
| **True Positives (TP)** | **36** | High-impact financial fraud, prize sweepstakes, and phishing accurately caught |
| **False Positives (FP)** | **0** | **Zero False Positives:** No legitimate ham message was incorrectly flagged (0.00% FP rate) |
| **False Negatives (FN)** | **337** | 2000s UK carrier marketing ads and ringtone subscriptions |
| **True Negatives (TN)** | **2,413** | Clean civilian SMS messages correctly passed as benign |
| **Precision** | **1.0000 (100.0%)** | Perfect precision on held-out split; zero false alerts on legitimate correspondence |
| **Recall** | **0.0965 (9.65%)** | Reflects domain gap between 2000s UK carrier marketing and modern cybercrime |
| **F1-Score** | **0.1760** | Operational trade-off prioritizing zero false alarms on innocent messages |

##### Confusion Matrix on `sms_final.tsv`:
$$\begin{pmatrix} \text{TN}=2413 & \text{FP}=0 \\ \text{FN}=337 & \text{TP}=36 \end{pmatrix}$$

*Caveat:* The UCI SMS Spam corpus dates from the mid-2000s UK mobile era and contains substantial historical carrier marketing and ringtone subscription ads alongside financial prize scams.

---

#### (b) Developer Security Fraud Benchmark (`backend/data/fraud_cases.csv` — 45 Cases)
To assess operational efficacy against modern cybercrime schemes prevalent in India and international communication channels, a 45-message benchmark was created covering Indian banking KYC phishing, customs courier extortion, UPI refund scams, electricity bill disconnection threats, task/job scams directing to Telegram/WhatsApp, crypto extortion/ransomware demands, digit-substituted look-alike domains (`paypa1`, `g00gle`, `amaz0n`, `b1nance`), genuine bank OTPs, delivery updates, and conversational chats.

*Caveat on Benchmark Independence:* This benchmark was designed by the engineering team to evaluate coverage against specific known fraud vectors; it does not constitute an independent third-party evaluation.

| Class Group | Total Evaluated | Correctly Classified | Misclassified | Accuracy / Precision |
| :--- | :--- | :--- | :--- | :--- |
| **Malicious Fraud / Threats** | 23 | 23 (TP) | 0 (FN) | Recall: **100.00%** |
| **Legitimate Ham (OTPs / Chats)** | 22 | 22 (TN) | 0 (FP) | Specificity: **100.00%** |
| **Overall Benchmark** | **45** | **45** | **0** | **Accuracy: 100.0% (45/45)** |

- **Precision:** **100.00%** (23 TP / 23 Flagged) — **Zero False Positives:** Legitimate automated bank OTPs (SBI, HDFC, ICICI, Axis, Uber) and delivery notifications (Amazon, Flipkart, Blue Dart, Zomato, Blinkit) were **never flagged as fraud**.
- **Recall:** **100.00%** (23 TP / 23 True Fraud cases caught).
- **Macro F1-Score:** **1.0000 (100.00%)**.

---

## 5. Limitations & Scope Constraints

1. **Physical Threat Safety Net vs. Dataset Evaluation:**  
   Physical-harm rules are not claimed to be universally essential across this benchmark corpus. On `final.csv`, where the neural model already detected 20 of 29 threat instances, the rules added 0 additional true positives and 3 false positives (modestly reducing Threat F1 from 0.5405 to 0.5195). Instead, deterministic physical harm heuristics are intended as a targeted defensive safety net for severe threats that the English-only neural model may miss outside this dataset (e.g., novel phrasing, Roman-script Hinglish threats like *"jaan se maar dunga"*, and obfuscated/leetspeak text like *"k1ll urself"*). Because only 29 threat rows exist in `final.csv`, these safety-net rules are evaluated separately on dedicated stress tests (`test_detection_engine.py`, `hard_cases.csv`) and are strictly limited by the small threat sample size in standard benchmarks.
2. **Dataset Domain Coverage & Fraud Exclusion:**  
   The underlying test dataset originates from online discussion boards (Wikipedia talk pages / Jigsaw toxicity corpora) and **does not annotate phishing, financial scams, look-alike banking domains, or digital arrest schemes**. Consequently, ShieldAI's fraud and phishing detection capabilities are evaluated through dedicated security test suites (`test_phase3_api.py`, `sms_final.tsv`, `fraud_cases.csv`), brand-matching algorithms, and live threat-hunting telemetry rather than this text corpus.
3. **Multilingual & Script Support Policy:**  
   The underlying DistilBERT transformer was fine-tuned exclusively on an English corpus. ShieldAI provides calibrated support for **English and Roman-script Hinglish** (Hindi in Latin script).
   - **Language Identification Pipeline:** The engine employs a production language-identification library (`langdetect==1.0.9`). To protect Roman-script Hinglish from false positive language classification, text is first checked against the South Asian Hinglish lexicon. When another language (Spanish, French, German, Italian, Portuguese) is detected with high confidence, the system returns `language_supported: false` and risk level `unsupported`.
   - **Language-Independent Security Fallback:** If an unsupported-language message contains a malicious or lookalike URL, URL shortener, cryptocurrency wallet, or phone-call extortion lure, the engine flags the real risk score ($\ge 50.0$) and category (`phishing`, `scam`, `threat`), while marking `language_supported: false`, ensuring threats are never marked "safe" merely because of language.
   - **Detected vs. Undetected Languages:** Spanish, French, German, Italian, Portuguese, and non-Latin scripts (Devanagari, Arabic, Cyrillic, etc.) are formally identified and marked unsupported. Languages without sufficient token markers may pass through the filter and cannot be certified safe.
4. **Hinglish Covered Exclusively via Rules:**  
   Roman-script Hindi abuse and intimidation phrases are identified through supplementary phonetic regex lists. The system lacks subword tokenization for complex, code-mixed bilingual grammar.
5. **Score Scale & Level Band Consistency:**  
   To preserve operational hierarchy in Trust & Safety triage, plain insults and cyberbullying are subject to a strict severity cap ($< 75.0$, default `plain_abuse_cap = 74.0`). Plain abuse can never produce scores near 100 with a "High" label. Critical level ($\ge 75.0$) is strictly reserved for actionable threats, sextortion blackmail, and high-confidence fraud.
6. **Edge-Case Evaluation Dataset:**  
   The `hard_cases.csv` dataset (passing 46 of 52 cases) is an internal stress-testing suite crafted by the authors to probe challenging boundary conditions (such as self-deprecation and sarcasm), not an externally certified academic standard.

---

## 6. Conclusion & Future Roadmap

ShieldAI establishes a functional, multi-layered defensive framework for detecting digital harassment and cyber extortion. By synthesizing deep neural representations with deterministic threat intelligence, client-side browser automation, and privacy-preserving incident management, ShieldAI demonstrates an effective operational methodology for Trust & Safety applications.

### Future Roadmap
1. **Multilingual Transformer Fine-Tuning:** Extend neural multi-label classification to vernacular South Asian languages using IndicBERT and XLM-RoBERTa.
2. **Multimodal Visual Forensics:** Integrate Vision Transformers (ViT) to perform automated forensic hash matching and deepfake artifact detection on attached screenshots and extortion media.
3. **Decentralized Threat Intelligence Sharing:** Implement STIX/TAXII threat intel feeds allowing decentralized Trust & Safety operations across institutions to share repeat offender indicators in real time.
