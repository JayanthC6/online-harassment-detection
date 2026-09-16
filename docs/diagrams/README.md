# ShieldAI Documentation Diagrams

This directory contains professional architectural and flow diagrams representing the exact implementation of the **ShieldAI** platform. These diagrams were generated for inclusion in the MCA final-year project report and presentation.

## Included Diagrams

### Architecture & Structure
1. **[01_overall_system_architecture](01_overall_system_architecture.mmd)** - High-level system architecture showing the React frontend, Flask backend, Neurosymbolic pipeline, Threat Intelligence feeds, and MongoDB. Useful for the "System Architecture" chapter.
2. **[02_use_case_diagram](02_use_case_diagram.mmd)** - Maps the user roles (End User vs. Admin) to their respective actions. Useful for the "Requirements Analysis" chapter.
3. **[03_class_diagram](03_class_diagram.mmd)** - UML Class diagram detailing the core services (`PredictionService`, `EvidenceService`) and ML Adapters (`MultilingualAdapter`, `DistilBertAdapter`). Useful for the "System Design" chapter.
4. **[04_dfd_level_0](04_dfd_level_0.mmd)** - Context-level Data Flow Diagram showing inputs and outputs relative to external entities. Useful for the "Data Flow" chapter.
5. **[05_dfd_level_1](05_dfd_level_1.mmd)** - Decomposed DFD showing the 8 primary internal processes of ShieldAI.
6. **[08_er_diagram](08_er_diagram.mmd)** - Entity-Relationship diagram showing the structure of the MongoDB collections (`users`, `history`, `actor_profiles`, `complaints`).
7. **[09_component_diagram](09_component_diagram.mmd)** - Component diagram mapping software modules across the client, backend, and external API boundaries.
8. **[10_deployment_diagram](10_deployment_diagram.mmd)** - Infrastructure layout showing how the browser, Chrome extension, local/cloud Python environment, and MongoDB interact. Useful for the "Deployment Setup" section.

### Sequence & Process Flows
9. **[06_sequence_text_analysis](06_sequence_text_analysis.mmd)** - Detailed sequence of operations when a user submits text. Shows the interaction between API, Multilingual translation, ML models, and Threat Intel. Useful for "Detailed Design".
10. **[07_sequence_file_analysis](07_sequence_file_analysis.mmd)** - File upload sequence showing modality extraction (`EasyOCR`, `Whisper`, `pdfplumber`).
11. **[11_activity_threat_analysis](11_activity_threat_analysis.mmd)** - Activity state diagram of the entire analysis lifecycle from input validation to saving to the database.

### Specialized Intelligence Workflows (Phase 6 / 7A)
12. **[12_multilingual_analysis_flow](12_multilingual_analysis_flow.mmd)** - Focused diagram on how NLLB-200 detects and translates non-English text while preserving PII.
13. **[13_threat_intelligence_flow](13_threat_intelligence_flow.mmd)** - Details the extraction of IOCs (Indicators of Compromise) and how they map to APIs like Google Safe Browsing and HIBP.
14. **[14_job_recruitment_intelligence_flow](14_job_recruitment_intelligence_flow.mmd)** - The logic flow for detecting Job/Recruitment scams within the Evidence Service.

## Formats
- **`.mmd` files:** The original, editable Mermaid source code.
- **`.png` files:** High-resolution rendered images suitable for direct embedding into Microsoft Word / PDF reports.
