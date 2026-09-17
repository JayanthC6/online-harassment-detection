# ShieldAI — Example Inputs and Expected Outputs

This document contains representative manual test cases for demonstrating the ShieldAI Online Harassment Detection and Digital Safety Analysis System. The expected results describe the intended behavior and should be interpreted together with the system's actual model confidence, risk score, and explainability output.

---

## 1. Clean / Safe Content

**Test ID:** DEMO-001  
**Feature:** Baseline NLP Classification (False Positive Prevention)  
**Example Input:**  
> "Please remember to use a strong password and enable two-factor authentication on your account to stay secure."

**Expected Classification/Result:**  
Clean / Safe.  
**What the examiner should observe:**  
The model correctly understands the semantic context and does not flag words like "password" as a threat. The risk score remains low (0-10) and no alerts are triggered.

---

## 2. Harassment / Offensive Content

**Test ID:** DEMO-002  
**Feature:** Toxic/Harassment Classification via Neural Engine  
**Example Input:**  
> "You're completely useless. Nobody wants you here. Delete your account and leave."

**Expected Classification/Result:**  
Harassment / Offensive language. Elevated risk score depending on neural confidence.  
**What the examiner should observe:**  
DistilBERT flags the semantic aggression. The Integrated Gradients token heatmap should highlight words like "useless" and "nobody wants you" as the primary drivers of the classification.

---

## 3. Direct Threat

**Test ID:** DEMO-003  
**Feature:** Physical Threat Detection  
**Example Input:**  
> "If you contact me again, I will hurt you. Stay away from me."

**Expected Classification/Result:**  
Threat detected with High/Critical risk score.  
**What the examiner should observe:**  
Both the neural model and the heuristic engine (Noisy-OR fusion) should flag this explicitly. The system should generate an Evidence Plan recommending immediate screenshot preservation and physical safety steps.

---

## 4. Extortion / Conditional Threat

**Test ID:** DEMO-004  
**Feature:** Grammatical Extortion Detection (Heuristic Rules)  
**Example Input:**  
> "I have access to your account. Give me your password or I will delete all your files."

**Expected Classification/Result:**  
Extortion / Threat with an elevated/high risk score.  
**What the examiner should observe:**  
The Heuristic Engine successfully matches the structured grammar pattern (`[Demand] + [Consequence]`). The examiner should see the "Extortion Indicators Detected" tag in the UI, proving the system does not rely solely on the neural model.

---

## 5. Cyber Threat

**Test ID:** DEMO-005  
**Feature:** Digital/Infrastructure Threat Recognition  
**Example Input:**  
> "I will break into your server tonight and delete the production database."

**Expected Classification/Result:**  
Cyber Threat / Threat-related classification.  
**What the examiner should observe:**  
The model correctly identifies a digital attack vector rather than a physical threat, demonstrating domain-specific cyber vocabulary understanding.

---

## 6. Phishing / Malicious Link

**Test ID:** DEMO-006  
**Feature:** Suspicious URL & Spam Classification  
**Example Input:**  
> "Your account has been suspended. Verify your password immediately at http://192.168.1.10/claim"

**Expected Classification/Result:**  
Spam / Phishing.  
**What the examiner should observe:**  
The ML model flags the phishing context. Simultaneously, the Threat Intelligence engine detects the raw IP-based URL (`192.168.1.10`), triggering an external intelligence warning in the dashboard.

---

## 7. Job / Recruitment Scam

**Test ID:** DEMO-007  
**Feature:** Recruitment Safety Intelligence  
**Example Input:**  
> "Congratulations! You have been selected for a Software Developer position. To confirm your joining, you must pay a refundable ₹4,999 registration and processing fee before joining. Contact our recruiter on WhatsApp or Telegram immediately."

**Expected Classification/Result:**  
Job / Recruitment Scam.  
**What the examiner should observe:**  
The Evidence Service detects multiple suspicious vectors: a "payment-before-joining" demand combined with "suspicious communication channels" (WhatsApp/Telegram). A specialized Recruitment Safety Plan is generated, advising the user not to send ID documents or money.

---

## 8. PII Detection

**Test ID:** DEMO-008  
**Feature:** Privacy Preservation and PII Masking  
**Example Input:**  
> "My email is test@example.com and my phone number is 9876543210. Someone is threatening me repeatedly."

**Expected Classification/Result:**  
PII detected; Threat flagged.  
**What the examiner should observe:**  
The system detects the email and phone number categories. The public API response demonstrates that raw PII is scrubbed (`sanitize_result_for_public`), showing the system prioritizes victim privacy.

---

## 9. Cybersecurity Awareness Content

**Test ID:** DEMO-009  
**Feature:** Contextual Nuance (Preventing ML Overfitting)  
**Example Input:**  
> "Phishing attacks often use fake login pages to trick users into revealing their passwords. Users should verify the website address before entering credentials."

**Expected Classification/Result:**  
Clean / Safe.  
**What the examiner should observe:**  
Even though the text contains words like "Phishing," "trick," and "passwords," the model understands the educational context. This proves the system is not a rigid keyword-blocker.

---

## 10. Multilingual Analysis (Phase 7A)

**Test ID:** DEMO-010A (Hindi)  
**Example Input:**  
> "अगर तुमने मुझे दोबारा धमकी दी तो मैं पुलिस में शिकायत करूंगा।"

**Test ID:** DEMO-010B (Kannada)  
**Example Input:**  
> "ನೀನು ಮತ್ತೆ ನನಗೆ ಬೆದರಿಕೆ ಹಾಕಿದರೆ ನಾನು ಪೊಲೀಸರಿಗೆ ದೂರು ನೀಡುತ್ತೇನೆ."

**Test ID:** DEMO-010C (Tamil)  
**Example Input:**  
> "நீ மீண்டும் என்னை மிரட்டினால் நான் காவல்துறையில் புகார் செய்வேன்."

**Test ID:** DEMO-010D (Telugu)  
**Example Input:**  
> "నువ్వు మళ్లీ నన్ను బెదిరిస్తే నేను పోలీసులకు ఫిర్యాదు చేస్తాను."

**Expected Classification/Result:**  
Language detected dynamically, translated to English via `NLLB-200`, and correctly classified through the English DistilBERT pipeline.  
**What the examiner should observe:**  
The system gracefully handles non-English inputs. The examiner should see the `translation_status` flag, the detected source language code, and the translated text driving the final threat score.

---

## 11. Conversation-Level Analysis

**Test ID:** DEMO-011  
**Feature:** Temporal Risk Trajectory and Actor Profiling  
**Example Input (Synthetic Chat Export):**  
> User A: "Send me the files."  
> User B: "No, I don't want to."  
> User A: "Give them to me now."  
> User B: "Stop threatening me."  
> User A: "If you don't send them, I'll destroy your account."

**Expected Classification/Result:**  
Conversation flagged. Actor-level breakdown identifies User A as the primary aggressor.  
**What the examiner should observe:**  
Instead of analyzing isolated strings, the Conversation Adapter processes the entire file. The dashboard shows an escalation timeline and calculates the highest flagged-message concentration for User A.

---

## 12. File / Document Analysis

**Test ID:** DEMO-012  
**Feature:** Document Parsing (`pdfplumber` / Modality Extraction)  
**Example Inputs (Use actual project assets):**  
> 1. `backend/clean_job_offer.pdf`  
> 2. `backend/suspicious_job_offer.pdf`

**Expected Classification/Result:**  
PDFs are parsed; text is extracted and scored identically to raw text input.  
**What the examiner should observe:**  
The system proves its multi-modal capabilities. The suspicious PDF will trigger the Job Scam heuristics, while the clean PDF will pass as safe.

---

## 13. Threat Intelligence

**Test ID:** DEMO-013  
**Feature:** Domain and URL Indicators of Compromise (IOCs)  
**Example Input:**  
> "Your account has been compromised. Verify immediately: http://192.168.1.10/claim or contact support@g00gle-security.com"

**Expected Classification/Result:**  
Threat Intelligence triggers for IP-based URL and Typosquatting.  
**What the examiner should observe:**  
The `ThreatIntelAdapter` operates independently of the ML model, flagging the deceptive domain structure (`g00gle` vs `google`) and the raw IP address, injecting these deterministic alerts into the incident report.

---

## 14. Mixed / Complex Case

**Test ID:** DEMO-014  
**Feature:** Neurosymbolic Noisy-OR Fusion (System Stress Test)  
**Example Input:**  
> "Urgent! Your job has been approved. Pay ₹4,999 today or your offer will be cancelled. Contact the recruiter only through Telegram at http://bit.ly/fakejob"

**Expected Classification/Result:**  
High Risk multi-vector alert.  
**What the examiner should observe:**  
This triggers nearly every system layer:
1. ML engine detects spam/urgency.
2. Job Intel detects "payment-before-joining" and "suspicious communication".
3. Threat Intel detects a URL shortener (`bit.ly`).
The Noisy-OR engine successfully fuses these disparate signals into a single, cohesive, high-confidence Risk Score.

---

> **Demonstration Note:**  
> During the viva/client demonstration, the examiner can select representative cases from different categories rather than executing every example. The examples are intended to demonstrate coverage of the major implemented capabilities without requiring live malicious attacks.
