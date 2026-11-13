# ShieldAI Documentation Diagrams

This directory contains professional architectural, behavioral, and data flow diagrams representing the exact implementation of the **ShieldAI** platform. These diagrams are formatted in Mermaid (`.mmd`) for version control, automated rendering, and direct inclusion in the MCA final-year project dissertation and viva presentation.

## Included Diagrams

### Architecture & System Structure
1. **[01_overall_system_architecture](01_overall_system_architecture.mmd)** — High-level neurosymbolic system architecture showing the React 18 frontend, Chrome MV3 extension, Flask REST gateway, DistilBERT + Heuristic fusion pipeline, Captum XAI attribution, multi-provider LLM router, and SQLite persistence.
2. **[02_use_case_diagram](02_use_case_diagram.mmd)** — Actor role mapping (End-User / Citizen / Victim vs. SOC Analyst / Administrator) detailing scanning, reporting, case triage, and offender intelligence workflows.
3. **[03_class_diagram](03_class_diagram.mmd)** — UML Class diagram detailing core architectural services (`PredictionService`, `ModelService`, `AdminService`, `GuidanceService`, `AuthService`).
4. **[04_dfd_level_0](04_dfd_level_0.mmd)** — Context-level Data Flow Diagram (DFD Level 0) illustrating the boundary between users, the ShieldAI platform, and external statutory helplines.
5. **[05_dfd_level_1](05_dfd_level_1.mmd)** — Decomposed Data Flow Diagram (DFD Level 1) tracking data transformation across input sanitization, neural inference, heuristic validation, risk calibration, and database logging.
6. **[08_er_diagram](08_er_diagram.mmd)** — Entity-Relationship (ER) diagram reflecting the SQLAlchemy relational schema (`reports`, `profiles`, `offenders`, `conversations`, `complaints`, `users`, `audit_logs`).
7. **[09_component_diagram](09_component_diagram.mmd)** — Component mapping across Client, API Security, Detection Engine, Incident Intelligence, and Data Access layers.
8. **[10_deployment_diagram](10_deployment_diagram.mmd)** — Physical deployment topology showing the client browser environment, host application server (Python WSGI + SQLite), and optional cloud LLM providers with offline fallback.

### Sequence & Process Workflows
9. **[06_sequence_text_analysis](06_sequence_text_analysis.mmd)** — Sequence flow for synchronous text analysis across authentication, PII masking, tokenization, neural inference, and risk scoring.
10. **[07_sequence_file_analysis](07_sequence_file_analysis.mmd)** — Multi-modal file ingestion flow (PDF parsing, OCR image extraction, chat export parsing).
11. **[11_activity_threat_analysis](11_activity_threat_analysis.mmd)** — Activity state diagram tracking an incident from submission through severity classification to escalation and reporting.

### Specialized Intelligence Workflows
12. **[12_multilingual_analysis_flow](12_multilingual_analysis_flow.mmd)** — Script detection, Romanized Hinglish vocabulary matching, and the "Fail-Closed" safety invariant for non-Latin text.
13. **[13_threat_intelligence_flow](13_threat_intelligence_flow.mmd)** — Indicator of Compromise (IOC) extraction (UPI addresses, shortened domains, phone numbers).
14. **[14_job_recruitment_intelligence_flow](14_job_recruitment_intelligence_flow.mmd)** — Logic flow for detecting job offer scams, registration fee demands, and fraudulent recruitment domains.

---

## Viewing & Rendering Diagrams
- **Mermaid Live Editor:** Open [mermaid.live](https://mermaid.live) and paste the contents of any `.mmd` file.
- **Markdown Preview:** Supported natively in GitHub, GitLab, VS Code (with Mermaid extension), and VitePress.
