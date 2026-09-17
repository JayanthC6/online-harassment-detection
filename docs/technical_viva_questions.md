# ShieldAI — Technical Viva Questions & Answers

This document prepares you for the MCA final-year project viva/presentation. It contains realistic examiner questions about the actual implementation of ShieldAI, structured with clear, technically accurate answers.

---

## PART A — Project Fundamentals

### Q1. What is ShieldAI?
**Answer:** ShieldAI is a production-grade digital forensics and cyber safety platform designed to detect, classify, and mitigate online harassment, phishing, scams, and social engineering attacks.
**ShieldAI-specific point:** It analyzes multi-modal inputs (text, documents, images, audio, conversations) to generate a Threat Hunt report with a tailored evidence preservation plan for victims.

### Q2. What problem does the project solve?
**Answer:** Standard keyword filters fail to understand the context of modern digital abuse, such as implicit threats, grammatical extortion, and recruitment scams. ShieldAI solves this by using AI to understand semantic context and behavior over time.
**ShieldAI-specific point:** It moves beyond simple "spam blocking" to actual forensic evidence gathering and safety planning.

### Q3. Why did you choose this problem?
**Answer:** Digital abuse and financial scams (especially job scams) are rising globally, with attackers using increasingly sophisticated tactics like social engineering. Current tools lack explainability and rarely provide the victim with actionable next steps.
**ShieldAI-specific point:** I wanted to build a holistic solution that not only detects the threat but guides the victim through the aftermath via an Evidence Playbook.

### Q4. Who are the intended users?
**Answer:** There are two primary users:
1. End-Users (Victims): Using the public Threat Hunt tool to check suspicious messages.
2. SOC Analysts/Moderators: Using the secure admin dashboard to monitor trends and actor profiles.
**ShieldAI-specific point:** The dual-persona architecture enforces strict RBAC (Role-Based Access Control) to keep these user experiences isolated and secure.

### Q5. What are the main modules?
**Answer:** 
1. The Frontend (React SPA).
2. The REST API Backend (Flask).
3. The Neurosymbolic Prediction Pipeline (DistilBERT + Heuristics).
4. The Threat & Job Intelligence Services.
5. The Evidence & Safety Planning Service.
**ShieldAI-specific point:** Each module is decoupled, allowing the ML pipeline to run independently of the database or external APIs.

### Q6. What makes this different from a simple spam classifier?
**Answer:** A basic spam classifier uses Naive Bayes or Bag-of-Words to look for isolated "bad words." ShieldAI uses a contextual transformer (DistilBERT) and looks for structural patterns (Heuristics) like payment demands.
**ShieldAI-specific point:** It also analyzes entire conversation timelines to profile actor behavior rather than just analyzing a single isolated message.

### Q7. What happens when a user submits a message?
**Answer:** The message hits the API, is routed to the `PredictionService`, undergoes PII masking, is checked by the `MultilingualAdapter` (translated if non-English), and then passed through the DistilBERT neural model and Heuristic rules. Threat Intelligence feeds are asynchronously polled. The results are fused using Noisy-OR, a safety plan is generated, and the JSON is returned to the frontend.
**ShieldAI-specific point:** The entire flow is synchronous for the user but highly modularized in the backend code.

---

## PART B — Architecture

### Q8. Why did you use an Adapter Pattern?
**Answer:** The Adapter Pattern allows us to wrap different prediction mechanisms (Neural, Heuristic, Multilingual, ThreatIntel) into a unified interface with a `.predict()` method.
**ShieldAI-specific point:** This allows the `PredictionService` to just call `.predict()` on a list of adapters without needing to know the complex internal logic of how DistilBERT or NLLB works.

### Q9. Why is the multilingual adapter placed before the existing prediction adapters?
**Answer:** The primary DistilBERT model and the heuristic regex rules are tuned for English text.
**ShieldAI-specific point:** By placing the `MultilingualAdapter` first, we translate regional text (Hindi, Tamil, etc.) into English. This allows us to reuse the powerful English models downstream without having to rebuild the entire pipeline for every new language.

### Q10. Why did you separate the PredictionService from the adapters?
**Answer:** Separation of concerns. The `PredictionService` is responsible for orchestrating the flow, applying the Noisy-OR fusion math, and returning the final dictionary. The adapters are strictly responsible for returning their individual prediction scores.
**ShieldAI-specific point:** This makes the codebase vastly easier to test and maintain.

---

## PART C — Machine Learning / NLP

### Q11. What is DistilBERT?
**Answer:** DistilBERT is a small, fast, cheap, and light Transformer model trained by distilling the BERT base model. It has 40% fewer parameters, runs 60% faster, but retains 97% of BERT’s language understanding capabilities.
**ShieldAI-specific point:** It is the primary engine of ShieldAI, allowing deep contextual understanding without requiring expensive cloud GPUs.

### Q12. What does fine-tuning mean?
**Answer:** Fine-tuning takes a pre-trained model (like DistilBERT, which understands general English) and trains it further on a smaller, specific dataset.
**ShieldAI-specific point:** We fine-tuned the model on cyberbullying, harassment, and scam datasets so it learns the specific vocabulary of digital abuse.

### Q13. What is an embedding?
**Answer:** An embedding is a vector (array of numbers) that represents the semantic meaning of a word or sentence in multi-dimensional space. Words with similar meanings have vectors that point in similar directions.
**ShieldAI-specific point:** ShieldAI relies on embeddings during its explainability phase (Integrated Gradients) to calculate which words contributed most to a threat score.

### Q14. What is multi-label classification?
**Answer:** Unlike multi-class classification (where an input can only be ONE category), multi-label classification means an input can belong to multiple categories simultaneously.
**ShieldAI-specific point:** A single message in ShieldAI can be simultaneously classified as `Extortion`, `Threat`, and `Profanity`.

### Q15. Why can a highly confident model still be wrong?
**Answer:** Neural models are statistical guessers. If a model encounters out-of-distribution data (a sentence structure it has never seen), it may confidently misclassify it due to a single overlapping keyword.
**ShieldAI-specific point:** This is exactly why we use a neurosymbolic approach: the heuristic engine acts as a safety net against model blindspots.

---

## PART D — Neurosymbolic AI

### Q16. What is neurosymbolic AI?
**Answer:** It is an architecture that combines neural networks (deep learning) with symbolic AI (deterministic logic, rules, or knowledge graphs).
**ShieldAI-specific point:** ShieldAI fuses DistilBERT (neural) with the `HeuristicMultiLabelAdapter` (symbolic rules).

### Q17. Why not use only DistilBERT?
**Answer:** Pure neural models struggle with highly rigid structural threats that they weren't explicitly trained on. They can suffer from false negatives if an attacker uses new slang or slightly alters a scam template.
**ShieldAI-specific point:** DistilBERT might miss a grammatically complex extortion threat, but our deterministic regex rules catch it instantly.

### Q18. How are neural and symbolic signals combined?
**Answer:** They are combined using **Noisy-OR Fusion**.
**ShieldAI-specific point:** Instead of a simple average (which suppresses strong signals if one engine is unsure), Noisy-OR mathematically ensures that if *either* engine is highly confident, the final fused confidence remains high.

### Q19. What problem did the original fusion weighting cause?
**Answer:** Originally, if the Heuristic engine fired a 90% threat score, but the Neural engine fired 10%, the average was 50%, causing the system to classify an explicit threat as "Clean."
**ShieldAI-specific point:** The implementation of Noisy-OR fixed this. Now, an explicit rule trigger guarantees a high final threat score regardless of neural uncertainty.

---

## PART E — Explainable AI

### Q20. What is Integrated Gradients?
**Answer:** Integrated Gradients is an explainability technique that attributes the prediction of a deep neural network back to its input features (words).
**ShieldAI-specific point:** We use it (via the Captum library) to generate token heatmaps, visually highlighting the exact words that caused DistilBERT to flag a message.

### Q21. What is the difference between model attribution and rule-based explanation?
**Answer:** Model attribution (Integrated Gradients) explains the "black box" neural math by calculating gradients. Rule-based explanation simply states which deterministic regex triggered.
**ShieldAI-specific point:** ShieldAI provides both in its UI so analysts have complete transparency.

---

## PART F — Multilingual Processing

### Q22. Why did you add multilingual support?
**Answer:** Because digital abuse in India frequently occurs in regional languages. A purely English model is blind to massive portions of actual real-world harassment.
**ShieldAI-specific point:** Phase 7A added support for Hindi, Kannada, Tamil, and Telugu via the NLLB-200 model.

### Q23. Why translate into English instead of retraining the classifier?
**Answer:** Training a massive polyglot classification model from scratch requires millions of rows of labeled toxic data in regional languages, which simply does not exist.
**ShieldAI-specific point:** Translating regional text to English allows us to leverage our highly accurate, already-trained English DistilBERT model.

### Q24. What is NLLB and why use it?
**Answer:** NLLB (No Language Left Behind) is an open-source translation model by Meta. We use the `nllb-200-distilled-600M` variant.
**ShieldAI-specific point:** We chose it because it excels at low-resource Indic languages and runs locally, preventing us from sending sensitive victim data to external third-party translation APIs.

### Q25. Why is the translation model loaded lazily?
**Answer:** The NLLB model is large (600M parameters) and takes up significant RAM.
**ShieldAI-specific point:** Lazy loading ensures the model is only loaded into memory the very first time a non-English message is received, drastically speeding up application boot time and saving RAM if only English messages are analyzed.

---

## PART G — Threat Intelligence

### Q26. How do you detect suspicious URLs?
**Answer:** The `ThreatIntelAdapter` extracts URLs via regex, and then analyzes them using multiple techniques.
**ShieldAI-specific point:** It checks against Google Safe Browsing, detects URL shorteners (e.g., bit.ly), flags raw IP-based URLs, and uses Levenshtein distance to detect typosquatting (e.g., `paypa1.com`).

### Q27. What is HIBP?
**Answer:** Have I Been Pwned. It is an API that tracks compromised email addresses.
**ShieldAI-specific point:** ShieldAI extracts emails from messages and queries HIBP to warn the user if the sender is using an email known to be associated with data breaches.

---

## PART H — Job / Recruitment Intelligence

### Q28. Why did you add job scam detection?
**Answer:** Job scams have a unique, devastating financial impact but often masquerade as highly polite, professional text, causing standard ML models to misclassify them as "Clean."
**ShieldAI-specific point:** We added specific logic in the `EvidenceService` to detect this domain-specific threat.

### Q29. How do you distinguish a suspicious recruitment message from normal content?
**Answer:** We look for contextual intersections. A normal job offer mentions roles and salaries. A scam mentions roles, but also demands a "security deposit" or "registration fee" and insists on communicating only via Telegram.
**ShieldAI-specific point:** It is the *combination* of these structural indicators that flags it as a scam, triggering a specialized Evidence Playbook.

---

## PART I — Conversation Intelligence

### Q30. Why analyze the whole conversation?
**Answer:** Harassment is often a pattern of escalating boundary violations, not just a single swear word.
**ShieldAI-specific point:** The `ConversationAdapter` processes exported WhatsApp logs to calculate a temporal risk trajectory, showing how the abuse escalated over time.

### Q31. What is actor-level analysis?
**Answer:** Instead of just flagging the conversation, the system counts the flagged messages per sender.
**ShieldAI-specific point:** This identifies the primary aggressor (the actor with the highest concentration of toxic messages), protecting victims who might just be defending themselves.

---

## PART J — Privacy and PII

### Q32. Why is PII masked before translation?
**Answer:** Personally Identifiable Information (Emails, Phone numbers) should never be passed through deep learning transformer models unnecessarily, as models can memorize or hallucinate tokens.
**ShieldAI-specific point:** Masking it locally before passing it to NLLB guarantees absolute data sanitization for the victim.

### Q33. What is the purpose of `sanitize_result_for_public`?
**Answer:** It ensures that when the API returns JSON to the frontend, raw PII belonging to the attacker or victim is removed or obfuscated.
**ShieldAI-specific point:** This prevents malicious actors from using our public API endpoint as a data-scraping tool.

---

## PART K — Authentication and RBAC

### Q34. What is RBAC?
**Answer:** Role-Based Access Control. It restricts system access based on the role of the user (e.g., Admin vs Standard User).
**ShieldAI-specific point:** In ShieldAI, the public Threat Hunt tool requires zero authentication, but the SOC Dashboard requires a JWT token with Admin privileges.

### Q35. Why should authorization be enforced at the backend?
**Answer:** If you only hide the dashboard UI in React, an attacker can still send HTTP requests directly to the API endpoints using Postman or cURL.
**ShieldAI-specific point:** Flask enforces JWT verification on every protected route, ensuring true security at the API level.

---

## PART L — Database

### Q36. Which database does ShieldAI use and why?
**Answer:** ShieldAI uses MongoDB (via PyMongo).
**ShieldAI-specific point:** As a NoSQL document database, it is perfect for storing highly unstructured, nested JSON data (like our complex prediction results containing varied threat intel arrays and evidence playbooks).

### Q37. What data is persisted?
**Answer:** The `history` collection stores incident reports (text, scores, tier). The `actor_profiles` collection stores behavioral profiles of repeat offenders. The `complaints` collection stores user-submitted reports.
**ShieldAI-specific point:** If a user selects "Private Analysis" in the UI, the backend actively intercepts the request and ensures absolutely nothing is persisted to the database.

---

## PART M — Backend / FastAPI (Flask)

*(Note: ShieldAI actually uses Flask for its REST API, not FastAPI, though the architecture is modern and RESTful.)*

### Q38. Why separate routes from services?
**Answer:** Routes should only handle HTTP logic (parsing JSON, returning 200/400 codes). Services should handle business logic.
**ShieldAI-specific point:** `routes_public.py` calls `prediction_service.py`. This allows us to theoretically trigger a prediction from a background task or a CLI script without needing an HTTP request.

### Q39. What happens if the translation model fails?
**Answer:** We employ graceful degradation. The `MultilingualAdapter` wraps the translation in a try-except block.
**ShieldAI-specific point:** If it fails, the system falls back to processing the raw original text through the prediction pipeline and sets the `translation_status` flag to "failed", ensuring the app never crashes.

---

## PART P — Error Handling and Resilience

### Q40. How did you handle the Windows `WinError 32` file locking issue?
**Answer:** Windows strictly prevents a file from being read by a secondary process if the primary process hasn't closed its write handle.
**ShieldAI-specific point:** When downloading files for `pdfplumber` or `Whisper`, we explicitly call `tmp.close()` before passing the file path to the external libraries, fixing a major stability bug.

---

## PART U — Future Scope

### Q41. What is the biggest limitation of your current multilingual approach?
**Answer:** While NLLB-200 is great at native scripts (e.g., Devanagari Hindi), it struggles with Romanized code-switching (e.g., Hinglish written in English characters).
**ShieldAI-specific point:** Future scope (Phase 7B) would involve integrating a natively trained Indic transformer like MuRIL instead of relying entirely on translation.

---

## PART V — Rapid-Fire Viva Questions

1. **What is NLP?** Natural Language Processing; teaching computers to understand human language.
2. **What is ML?** Machine Learning; systems that learn patterns from data instead of explicit programming.
3. **What is a transformer?** A deep learning architecture that uses self-attention to understand context in sequences (like text).
4. **What is an adapter pattern?** A design pattern that allows classes with incompatible interfaces to work together.
5. **What is REST?** Representational State Transfer; an architectural style for APIs using HTTP methods.
6. **What is JWT?** JSON Web Token; a secure string used for stateless authentication.
7. **What is RBAC?** Role-Based Access Control.
8. **What is PII?** Personally Identifiable Information (emails, phone numbers).
9. **What is OCR?** Optical Character Recognition; extracting text from images (ShieldAI uses EasyOCR).
10. **What is an embedding?** A numerical vector representing semantic meaning.
11. **What is fine-tuning?** Retraining a pre-trained model on domain-specific data.
12. **What is multi-label classification?** Assigning multiple categories to a single input.
13. **What is Noisy-OR?** A probabilistic formula used to fuse confidence scores without artificially suppressing strong signals.
14. **What is explainable AI?** AI whose decision-making process can be understood by humans.
15. **What is Integrated Gradients?** An explainability algorithm that attributes a prediction to specific input tokens.
16. **What is threat intelligence?** External context (like domain reputation) used to enrich security analysis.
17. **What is typosquatting?** Registering a domain name very similar to a popular brand (e.g., google vs g00gle) to trick users.
18. **What is HIBP?** Have I Been Pwned; an API to check if an email was in a data breach.
19. **What is NLLB?** No Language Left Behind; Meta's multilingual translation model.
20. **What is lazy loading?** Loading a heavy resource (like an ML model) only when it is explicitly needed.
21. **What is a fallback?** A backup mechanism when a primary system (like translation) fails.
22. **What is regression testing?** Testing to ensure new code changes haven't broken existing functionality.
23. **What is an API?** Application Programming Interface; a way for software programs to talk to each other.
24. **What is authentication?** Verifying WHO a user is (Login).
25. **What is authorization?** Verifying WHAT a user is allowed to do (Admin access).
26. **What is a primary key?** A unique identifier for a database record (e.g., MongoDB `_id`).
27. **What is a foreign key?** A field linking one table/collection to another (e.g., `user_id` in the history collection).
28. **What is normalization?** Organizing database data to reduce redundancy.
29. **What is Groq?** The ultra-fast LLM API provider used for ShieldAI's safety chatbot.
30. **What is pdfplumber?** A Python library used in ShieldAI to extract text from PDF documents.
31. **What is Whisper?** OpenAI's speech-to-text model used for audio processing in ShieldAI.
32. **What is a NoSQL database?** A non-relational database (like MongoDB) that stores data in documents rather than strict tables.
33. **What is React?** A JavaScript library for building user interfaces (ShieldAI's frontend).
34. **What is Vite?** A fast build tool and development server used for the React frontend.
35. **What is CORS?** Cross-Origin Resource Sharing; a security feature that allows the frontend to talk to the backend on a different port.
36. **What is a Promise in JavaScript?** An object representing the eventual completion or failure of an asynchronous operation (like an API call).
37. **What is a Virtual Environment in Python?** An isolated environment to manage project-specific dependencies.
38. **What is an epoch?** One complete pass of the training dataset through a machine learning model.
39. **What is an F1 score?** The harmonic mean of precision and recall, used to measure model accuracy.
40. **What does pip do?** It is the package installer for Python (`requirements.txt`).

---

## PART W — Difficult Examiner Questions

**Q1. "If DistilBERT already detects threats, why do you need heuristics?"**
**Answer:** DistilBERT is excellent at semantic context, but it generalizes. It can miss highly specific, rigid structural scams (like a job offer demanding a "security deposit"). Heuristics provide a deterministic safety net for threats that require zero-tolerance detection.

**Q2. "Why don't you simply translate every message?"**
**Answer:** Because translating native English text through a multilingual model introduces unnecessary latency, wastes CPU/RAM, and can cause translation artifacts that degrade the text quality before it reaches the classifier.

**Q3. "Why didn't you train a separate model for every Indian language?"**
**Answer:** Training a deep learning model requires vast amounts of high-quality labeled data (tens of thousands of toxic/clean examples per language). Such datasets do not exist for most regional Indian languages. Translating to English leverages the powerful English dataset we already have.

**Q4. "How do you prevent heuristic rules from causing false positives?"**
**Answer:** We design the rules structurally, not as simple keyword matches. For example, the extortion rule doesn't just trigger on the word "bitcoin". It looks for a sequence: a demand (`pay me`), a currency (`bitcoin`), and a consequence (`or I will leak`).

**Q5. "Why did you change the Noisy-OR weighting in Phase 7A?"**
**Answer:** The original fusion algorithm averaged the scores. This suppressed highly explicit threat signals from the heuristic engine if the neural model was unsure. Changing it to Noisy-OR ensures that explicit rule matches guarantee a high final risk score.

**Q6. "How do you know your model is not just memorizing keywords?"**
**Answer:** We evaluated the model using Integrated Gradients (Explainability). By analyzing the token heatmaps, we confirmed the model was looking at the surrounding context (e.g., the aggression in the verb) rather than just triggering on isolated bad words.

**Q7. "Why can't frontend RBAC alone protect admin endpoints?"**
**Answer:** Hiding a button in React does not secure a system. An attacker can inspect the network tab, find the API endpoint URL, and send a raw HTTP request. Backend route protection (JWT verification) is the only true security.

**Q8. "What happens if a user submits a safe cybersecurity-awareness message containing words such as 'password', 'hack', or 'attack'?"**
**Answer:** Because DistilBERT is a contextual transformer, it understands the surrounding semantics. It learns that "How to protect your password from a hack" is educational, whereas "Give me your password or I will hack you" is a threat. A simple keyword filter would fail this test.

**Q9. "What is the biggest limitation of your current multilingual approach?"**
**Answer:** It struggles with code-switching and Romanized text (e.g., Hinglish). NLLB expects native scripts.

**Q10. "Why is risk score separate from classification?"**
**Answer:** Classification categorizes the threat (e.g., Identity Attack), while Risk Score quantifies severity. An identity attack involving a malicious payload (detected via Threat Intel) has a much higher Risk Score than an identity attack without a payload, even though the classification is the same.

---

## PART X — Project-Specific "Explain This Code" Questions

### 1. `backend/ml/adapters/heuristic.py`
**What is its purpose?** It applies deterministic regex rules to incoming text to flag specific structural threats.
**Why does it exist?** To act as a safety net for edge-case threats that the neural model misses.
**What happens if it fails?** It returns an empty dictionary of scores (`{}`) so it doesn't crash the pipeline.

### 2. `backend/ml/adapters/multilingual.py`
**What is its purpose?** It detects the language of the text, masks PII, and translates non-English text to English using NLLB-200.
**Why was it designed this way?** Built as an Adapter, it keeps translation logic completely isolated from the prediction logic.
**What are its important methods?** `_detect_and_translate()`, `mask_pii()`.

### 3. `backend/api/routes_public.py`
**What is its purpose?** It handles unauthenticated HTTP POST requests from the public Threat Hunt tool.
**What happens when `/predict/file` is called?** It saves the uploaded file to a temporary location, routes it to the specific modality extractor (e.g., `pdfplumber` or `whisper`), passes the extracted text to `prediction_service.predict_text`, explicitly closes the temporary file to prevent Windows locking errors, and returns the sanitized JSON.

---

# Last-Minute Viva Revision

### Project in 30 seconds
"ShieldAI is a multi-modal digital forensics platform that detects online harassment, phishing, and scams. It uses a neurosymbolic approach—combining a fine-tuned DistilBERT neural model with a deterministic rules engine—and integrates threat intelligence to provide victims with tailored evidence preservation plans."

### Architecture in 30 seconds
"The user interacts with a React frontend. The request hits a Flask backend where the text is translated if necessary via NLLB-200, then analyzed by both DistilBERT and a Heuristic engine. Threat Intelligence APIs are polled asynchronously. The scores are fused using Noisy-OR, an Evidence Plan is generated, and the results are stored in MongoDB."

### ML in 30 seconds
"We use DistilBERT because transformers understand context far better than basic keyword filters. However, because deep learning can miss rigid scam templates, we fuse it with a Heuristic Rules Engine to guarantee detection of explicit threats."

### Multilingual in 30 seconds
"We use `langdetect` to check the language. If it's English, we bypass translation. If it's regional, we mask PII for privacy, and translate it to English locally using the NLLB-200 model, allowing us to leverage our highly accurate English prediction pipeline."

### Security in 30 seconds
"PII is masked before any deep-learning processing occurs. The system supports a 'Private Analysis' flag which bypasses database persistence entirely. Admin endpoints are strictly protected by JWT authentication on the Flask backend."

### Explainability in 30 seconds
"We use Integrated Gradients to calculate token attribution. This visualizes exactly which words drove the neural model's prediction, ensuring our trust & safety decisions are transparent and not a black box."

### Biggest technical challenge
"Managing the fusion of the neural and symbolic engines. Originally, unsure neural scores were dragging down explicit heuristic flags, causing false negatives for severe threats. We solved this by implementing a probabilistic Noisy-OR fusion algorithm."

### Biggest limitation
"The NLLB-200 translation model excels at native Indic scripts but struggles with Romanized code-switching like Hinglish. Phase 7B would aim to replace the translation adapter with a natively trained Indic transformer like MuRIL."
