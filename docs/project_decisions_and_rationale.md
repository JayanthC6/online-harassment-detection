# ShieldAI — Project Decisions & Rationale

## 1. Project Overview
ShieldAI is a comprehensive digital forensics and cyber safety platform designed to detect, classify, and mitigate online harassment, cyberbullying, phishing, scams, and social engineering attacks. 
It addresses the growing issue of digital abuse where traditional keyword filters fail to understand the nuance of modern threats.
The system is built for two distinct users:
- **End Users (Victims):** Who use the public "Threat Hunt" console to analyze messages and receive actionable safety plans.
- **SOC Analysts / Admins:** Who use the secure dashboard to monitor platform abuse, track repeat offenders, and review intelligence metrics.

ShieldAI uses a **Neurosymbolic approach** (combining Machine Learning with deterministic rules), enriched by external Threat Intelligence, to provide high accuracy, explainability, and actionable evidence guidance.

---

## 2. Why ShieldAI Uses a Neurosymbolic Approach
A purely neural approach (Machine Learning only) struggles with deterministic, rigidly structured threats (like grammatical extortion or specific scam templates) and often lacks explainability. Conversely, a purely symbolic approach (Keyword/Regex rules only) is rigid, easily bypassed by typos, and fails to understand semantic intent or context.

ShieldAI combines both:
- **Machine Learning (DistilBERT):** Understands semantic context, implicit threats, and nuanced toxic behavior.
- **Deterministic Heuristics:** Instantly flags rigid structural threats (e.g., "pay me $500 or I will leak your photos") that neural models might under-score due to lack of training data.

This hybrid approach improves domain-specific detection, reduces false negatives for severe threats, and provides robust explainability.

---

## 3. Why DistilBERT Was Used
DistilBERT is a distilled version of the BERT transformer architecture. 
- **Efficiency vs. Accuracy:** It retains 97% of BERT's language understanding capabilities while being 60% faster and 40% smaller. This allows the model to run locally and rapidly without requiring massive GPU clusters.
- **Contextual Understanding:** As a transformer, it uses self-attention to understand the relationship between words in a sentence, which is vastly superior to traditional Bag-of-Words (TF-IDF) models that ignore word order.
- **Fine-Tuning:** Fine-tuning DistilBERT allowed the project to teach the model the specific nuances of digital abuse rather than relying on generic sentiment analysis.

---

## 4. Why Heuristic Rules Were Added
Despite the power of DistilBERT, deterministic rules were necessary to capture domain-specific structural patterns. 
For example, extortion often relies on a clear grammatical structure: `[Demand/Action] + [Threat/Consequence]`. A neural model might miss this if it hasn't seen the exact phrasing. 

The `HeuristicMultiLabelAdapter` implements rules for:
- Urgency and high-pressure tactics.
- Extortion and blackmail mechanics.
- Job and recruitment scam indicators (e.g., "registration fee required").
- Explicit physical threats.

**Design Principle:** Rules are designed to capture structural syntax and behavioral patterns, rather than acting as a giant, easily bypassed dictionary of bad words.

---

## 5. Why Neural + Heuristic Fusion Was Used
ShieldAI uses a **Noisy-OR Fusion Engine** to combine the neural confidence scores with the deterministic heuristic signals. 

In earlier iterations, a prediction issue was discovered: strong heuristic signals for explicit threats were being artificially suppressed if the neural model was unsure (resulting in a low average score).

The Noisy-OR logic corrects this: it treats the neural and heuristic engines as independent probability signals. If *either* engine strongly detects a threat, the final fused confidence remains high. This ensures that explicit threats are never artificially downgraded just because one engine missed them.

---

## 6. Why Multilingual Support Was Added
During Phase 7A, multilingual support was added targeting English, Hindi, Kannada, Tamil, and Telugu. 
As an Indian digital-safety application, ShieldAI must handle the linguistic diversity of its user base. Regional languages are increasingly weaponized for cyberbullying, scams, and harassment. Without multilingual support, the system would be blind to a vast portion of regional threats.

---

## 7. Why a Multilingual Adapter Was Chosen
The multilingual capability is implemented via the **Adapter Pattern** (`MultilingualAdapter`).

**Flow:** Input → MultilingualAdapter → HeuristicMultiLabelAdapter → PrimaryModelAdapter (DistilBERT)

Instead of rewriting the core `PredictionService` or training a massive polyglot model from scratch, the `MultilingualAdapter` intercepts incoming text, translates it to English, and passes it down the existing pipeline. 
**Benefits:**
- **Separation of Concerns:** The core prediction logic remains unaware of the translation layer.
- **Reuse:** We maximize the ROI of the highly accurate English DistilBERT model.
- **Modularity:** It seamlessly supports both single-message and conversation-level parsing without architectural disruption.

---

## 8. Why Language Detection Is Performed Before Translation
The `MultilingualAdapter` uses the `langdetect` library to determine the source language before taking action.
- If the text is English (`'en'`), translation is entirely bypassed, saving significant CPU/memory resources and reducing latency.
- If the language is unsupported or too short to detect accurately, it falls back to the original text.
Blindly translating all text would waste computational resources and potentially degrade native English inputs through unnecessary round-trip translation artifacts.

---

## 9. Why NLLB Was Selected for Translation
The project utilizes `facebook/nllb-200-distilled-600M` (No Language Left Behind) for translation.
- **Coverage:** NLLB supports over 200 languages, heavily featuring low-resource Indic languages (Hindi, Kannada, Tamil, Telugu).
- **Offline/Privacy:** Running NLLB locally ensures that sensitive victim data is never sent to a third-party translation API (like Google Translate), maintaining strict privacy.
- **Trade-off:** The 600M parameter model requires a significant initial download and utilizes more local memory, but this is an acceptable trade-off for data sovereignty and privacy.

---

## 10. Why PII Is Masked Before Translation
**Flow:** Native-language input → PII masking → Translation → Analysis.

This is a critical security and privacy decision. Personally Identifiable Information (Emails, Phone numbers) is stripped out of the text *before* it is passed to the translation model. 
Raw PII should not be passed through transformer models unnecessarily, as models can sometimes hallucinate, alter, or memorize tokens. Masking it first ensures strict data sanitization and protects the victim's identity throughout the pipeline.

---

## 11. Why Translation Failure Has a Graceful Fallback
If the NLLB model fails to load, runs out of memory, or encounters untranslatable text, the `MultilingualAdapter` catches the exception and falls back to passing the raw, original text to the prediction pipeline. 
The system is designed so that a translation subsystem failure does not crash the core application. The final output includes a `translation_status` flag indicating whether the text was translated, bypassed, or failed.

---

## 12. Why Threat Intelligence Was Added
Text classification alone cannot determine if a URL is a live phishing site or if an email belongs to a known threat actor. 
ShieldAI integrates asynchronous Threat Intelligence to enrich the context:
- **Google Safe Browsing API:** Checks extracted URLs for malware/phishing.
- **Have I Been Pwned (HIBP):** Checks extracted emails for breach history.
- **Domain/WHOIS Intelligence:** Flags domains registered less than 30 days ago.
- **Typosquatting & IP URLs:** Detects deceptive links (e.g., `paypa1.com`) and raw IP addresses used by attackers to hide domains.

---

## 13. Why Threat Intelligence Is Appended After Core Prediction
Threat Intelligence is modularized in the `ThreatIntelAdapter` and its results are appended to the prediction *after* the core ML classification.
- **Modularity:** APIs can fail, rate-limit, or timeout. By keeping this layer separate, API failures do not block the ML classification.
- **Maintainability:** New threat feeds can be added without altering the DistilBERT weights or the heuristic rules.

---

## 14. Why Conversation-Level Analysis Was Added
Analyzing a single isolated message (e.g., "I'm waiting outside") might yield a low risk score. However, analyzing a full exported WhatsApp or Instagram conversation reveals the temporal trajectory of abuse. 
Conversation-level analysis uncovers concentrated harassment, grooming behaviors, and repeated boundary violations over time that single-shot analysis inherently misses.

---

## 15. Why Actor-Level Analysis Was Added
When a conversation is uploaded, the system identifies the "Actor with highest flagged-message concentration."
Rather than just flagging the chat as "Toxic", the system isolates *who* is driving the toxicity. This provides actionable intelligence for moderators and investigators, allowing them to focus on the aggressor rather than penalizing the victim defending themselves.

---

## 16. Why Explainability Was Added
In digital forensics and Trust & Safety, a black-box response of "Threat Detected: 95%" is insufficient. Moderators need to know *why* a decision was made to avoid bias and justify account bans or legal escalations.
ShieldAI provides explainability via:
- Token-level model attribution.
- Deterministic heuristic triggers (e.g., "Flagged due to Job Scam Indicators").
- Explicit Threat Intelligence matches (e.g., "URL matched Google Safe Browsing").

---

## 17. Why Integrated Gradients Was Used
*(Note: Captum explainability is part of the architecture design for transformer attribution).*
Integrated Gradients is used to attribute the model's prediction back to the original input tokens. By comparing the text embeddings to a baseline (zero tensor), the system can highlight exactly which words (e.g., "kill", "scam") drove the neural model's decision, providing a transparent "Token Heatmap" to the analyst.

---

## 18. Why Job / Recruitment Intelligence Was Added
Job scams require highly specific domain logic. ShieldAI's `EvidenceService` explicitly scans for recruitment indicators:
- Demands for "registration fees" or "security deposits".
- Over-reliance on "WhatsApp only" or "Telegram" for official hiring.
- "Guaranteed hiring" without interviews.
Because these scams are financially devastating, they are treated with domain-specific logic rather than generic spam filters, ensuring victims get tailored warnings.

---

## 19. Why Personalized Safety & Evidence Plans Were Added
Detecting a threat is only half the battle; victims often don't know what to do next. 
ShieldAI generates a structured Evidence Plan tailored to the specific incident tier (e.g., Blackmail vs. Phishing). These plans offer immediate safety actions, psychological support guidance, and next steps for reporting to authorities.

---

## 20. Why Evidence Preservation Guidance Exists
Victims of digital abuse often panic and delete the abusive messages or block the sender immediately, inadvertently destroying critical forensic evidence.
The Evidence Plan explicitly instructs users on how to preserve timestamps, URLs, payment hashes, and take verifiable screenshots *before* blocking the attacker, ensuring the data is admissible for future investigations.

---

## 21. Why Authentication and RBAC Were Implemented
Role-Based Access Control (RBAC) separates the public victim portal from the Cyber SOC Dashboard.
- **End Users:** Do not require accounts to access the Threat Hunt tool, ensuring zero friction for victims seeking help.
- **Admins/Analysts:** Require secure JWT authentication to view aggregated platform analytics, manage behavioral profiles, and review the incident queue, ensuring strict data privacy.

---

## 22. Why Private Analysis Exists
The public Threat Hunt tool includes a toggle: "Keep this analysis private (Do not save to history)."
If a victim is analyzing highly sensitive material (e.g., checking if an email is a sextortion scam), they may not want the platform administrators to see it. Honoring this privacy flag ensures the data is processed in-memory and immediately discarded, never persisting to the MongoDB database.

---

## 23. Why PII Sanitization Exists in Public Responses
Even when an incident is saved to the database for administrative review, the JSON response sent back to the public frontend is passed through a `sanitize_result_for_public` function. This strips raw PII (like the attacker's email or phone number) from the network payload. This ensures that the public API cannot be abused to scrape or expose sensitive information.

---

## 24. Why Risk Scoring Is Separate from Classification
Classification answers: *"What is this?"* (e.g., Extortion, Phishing).
Risk Scoring answers: *"How dangerous is this right now?"* (0-100 score).

Separating these concepts allows ShieldAI to assign a base severity to a category (Extortion = Critical) but dynamically increase the Risk Score if a multi-vector attack is detected (e.g., Extortion + Malicious URL + Spoofed Domain).

---

## 25. Why the Existing Risk-Scoring Algorithm Was Preserved
During Phase 7A's prediction improvements, the underlying Risk Scoring mathematical formula was deliberately preserved. 
Modifying the risk weights would have invalidated historical data and dashboard analytics. By fixing the prediction detection at the model level (Noisy-OR fusion) rather than hacking the risk-score calculator, backward compatibility and dashboard stability were maintained.

---

## 26. Why the System Does Not Use an LLM as the Primary Prediction Engine
While ShieldAI uses Groq (an LLM) for chatbot support and complaint summarization, it does **not** use an LLM for the core prediction engine.
- **Latency & Cost:** LLMs are too slow and expensive to process thousands of real-time messages (e.g., scanning a live WhatsApp Web feed via the Chrome Extension).
- **Determinism:** LLMs are prone to hallucinations and prompt-injections. DistilBERT + Heuristics guarantees predictable, mathematically reproducible classifications required for forensic logging.

---

## 27. Why Features Were Added Incrementally
ShieldAI was built in phases to protect existing stability. 
For example, Multilingual support was added as an Adapter. This allowed the English ML models to remain untouched while adding a new feature layer. This modular design principle ensures that an issue in a new feature (like a translation failure) does not break the core application.

---

## 28. Major Problems Encountered and Why the Solutions Were Chosen

| Problem | Root Cause | Decision | Why This Solution | What Was Preserved |
|---------|------------|----------|-------------------|---------------------|
| Explicit threats scoring too low | Neural model suppressed heuristic triggers if it was unsure | Implemented Noisy-OR Fusion | Treats engines as independent signals; if either fires high, the score stays high. | The neural model weights were preserved without retraining. |
| Non-English abuse bypassing detection | DistilBERT was trained primarily on English | Added NLLB-200 via `MultilingualAdapter` | Translates text to English dynamically, maintaining pipeline integrity. | The highly accurate English DistilBERT model was preserved. |
| Windows `WinError 32` file locking | `tempfile.NamedTemporaryFile` was being accessed by external processes (pdfplumber/whisper) while open | Explicitly close `tmp.close()` before parsing | Windows requires file handles to be released before other processes can read them. | The modality extraction architecture was preserved. |
| Job Scams slipping through | ML models viewed them as generic spam, missing financial impact | Added domain-specific Job Scam regex heuristics | Scams have rigid structures (fees, guaranteed hiring) best caught by deterministic rules. | The core ML dataset didn't need expensive retraining. |

---

## 29. Important Trade-offs
- **Local Models vs. Cloud APIs:** NLLB-200 and Whisper run locally to ensure absolute data privacy. The trade-off is higher local memory usage and longer initial download times.
- **Accuracy vs. Deterministic Control:** Neural models offer semantic nuance, but Heuristics offer rigid, guaranteed detection. ShieldAI accepts the complexity of maintaining two engines in exchange for catching both implicit and explicit threats.

---

## 30. Current Limitations
*(Based on the current implemented architecture)*
- **Romanized Code-Switching:** NLLB-200 is excellent at native scripts (Hindi in Devanagari) but may struggle with highly colloquial Hinglish (Hindi written in the English alphabet).
- **Translation Nuance:** Sarcasm or cultural idioms in Telugu or Kannada may lose their original toxic intent when translated to English before classification.
- **Hardware Requirements:** Running DistilBERT, NLLB-200, and Whisper locally requires a modern CPU and significant RAM, which may limit deployment on ultra-low-end hardware without transitioning to cloud infrastructure.

---

## 31. Future Scope
*(Not currently implemented)*
- **Native Indic Models:** Replacing the translation adapter with a natively trained multilingual DistilBERT model (e.g., MuRIL).
- **Audio Deepfake Detection:** Expanding Whisper's transcription to include voice-biometric spoofing detection.
- **Image Hash Banning:** Using perceptual hashing (PhotoDNA) to instantly flag known abusive images before running OCR.

---

## 32. Final Decision Summary

1. **Neurosymbolic Fusion:** Used to balance semantic understanding with strict, explainable rule enforcement. Protects against AI blindspots.
2. **DistilBERT Base:** Chosen for fast, local, privacy-first inference without relying on expensive LLMs.
3. **Multilingual Adapter (NLLB):** Added to support Indian languages without throwing away the existing English models.
4. **Threat Intel Decoupling:** API calls (Safe Browsing/WHOIS) are appended post-prediction so network failures don't crash the ML pipeline.
5. **Role-Based Access Control:** Protects sensitive analytics while keeping the threat-hunt tool frictionless for victims.
6. **PII Masking Pre-Translation:** Ensures strict data privacy and prevents sensitive data from leaking into translation buffers.
