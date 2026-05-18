# Requirements Document

## Introduction

ContractForge Auditor is a multi-agent AI platform for enterprise contract governance. Legal, procurement, and compliance teams routinely review long contracts against internal policy libraries, a slow and error-prone process. ContractForge Auditor ingests a contract and a policy document, runs a six-stage LangGraph agent pipeline powered by Google Gemini, and returns a structured governance report containing a risk score, a category heatmap, clause-level findings, policy violations, suggested amended clauses, and a what-if Risk Simulation panel for scenarios such as Force Majeure or Data Breach.

The product is built for two hackathon tracks:

- **Agent Security & AI Governance** — every agent invocation is logged in an auditable trail, model outputs are validated against strict Pydantic schemas, prompts include anti-injection guardrails, and PII is redacted from logs.
- **Gemini Agents** — the pipeline is composed of specialised Gemini-powered agents orchestrated through LangGraph, exercising Gemini's native PDF understanding, structured JSON output, and bilingual reasoning (English and Vietnamese).

The system ships as a FastAPI backend (Render or Fly.io) and a React 18 + Vite + TypeScript frontend (Vercel), with a Dockerfile, CORS configuration, environment example, and sample bilingual data set ready for demo.

## Glossary

- **Auditor_System**: The complete ContractForge Auditor application, comprising the FastAPI backend, the LangGraph agent pipeline, and the React frontend.
- **Backend_API**: The FastAPI service exposing the REST endpoints under `/api`.
- **Frontend_App**: The React 18 + Vite + TypeScript single-page application that renders the dashboard, simulation panel, and report viewer.
- **Agent_Pipeline**: The LangGraph orchestration that runs the six agents (Ingestion & Extraction, Clause Analysis, Policy Compliance & Mapping, Risk Simulation, Governance & Recommendation, Report Generation) in sequence.
- **Ingestion_Agent**: The first agent in the Agent_Pipeline; parses Contract and Policy inputs and segments the contract into Clauses.
- **Clause_Analysis_Agent**: The agent that classifies and summarizes each Clause.
- **Policy_Mapping_Agent**: The agent that maps each Clause to zero or more Policy Rules and flags Violations.
- **Risk_Simulation_Agent**: The agent that evaluates predefined What-If Scenarios against the contract.
- **Recommendation_Agent**: The agent that produces suggested amended Clauses.
- **Report_Agent**: The agent that assembles the final Governance Report.
- **Clause**: A discrete contractual provision identified by a stable clause identifier, with an original text span and a detected language tag (`en` or `vi`).
- **Policy Rule**: A single rule extracted from the uploaded policy file, with an identifier, a natural-language description, and a Risk Category tag.
- **Risk Category**: One of the fixed English-keyed categories `legal`, `financial`, `operational`, `compliance`, `data_privacy`.
- **Risk Score**: An integer from 0 to 100 representing overall contract risk, where 0 is lowest risk and 100 is highest risk.
- **Per-Category Score**: An integer from 0 to 100 computed for each Risk Category.
- **What-If Scenario**: A named hypothetical condition the Risk_Simulation_Agent evaluates against the contract; the MVP set is `force_majeure`, `penalty_delay`, `data_breach`, `termination`, `payment_default`.
- **Violation**: A finding emitted by the Policy_Mapping_Agent linking a Clause to a Policy Rule with a severity level (`low`, `medium`, `high`, `critical`).
- **Audit Trail Entry**: A persisted record produced for each agent invocation containing agent name, input hash, output hash, ISO-8601 timestamp, Gemini model version, and latency in milliseconds.
- **Governance Report**: The final structured artifact returned by the Report_Agent, containing executive summary, Risk Score, Per-Category Scores, clause table, Violations, recommendations, and audit trail appendix.
- **Analysis Job**: A single end-to-end run of the Agent_Pipeline against one Contract and one Policy upload, identified by a `job_id` (UUID v4).
- **Anti-Injection Guardrail**: A fixed prefix in every system prompt that instructs the agent to ignore embedded instructions in user content and to emit only schema-conformant JSON.

## Requirements

### Requirement 1: File Upload and Ingestion

**User Story:** As a compliance analyst, I want to upload a contract and a policy file in English or Vietnamese, so that the Auditor_System can analyze them together.

#### Acceptance Criteria

1. WHEN a client sends a `POST /api/upload` request with a `contract` file part and a `policy` file part, THE Backend_API SHALL persist both files, assign a `job_id` UUID v4, and return HTTP 200 with a JSON body containing `job_id`, `contract_filename`, `policy_filename`, and `detected_language`.
2. THE Backend_API SHALL accept contract uploads with MIME type `application/pdf` or `text/plain`.
3. THE Backend_API SHALL accept policy uploads with MIME type `application/pdf`, `text/csv`, or `text/plain`.
4. IF an uploaded file exceeds 15 megabytes, THEN THE Backend_API SHALL reject the request with HTTP 413 and a JSON error body containing `error_code` `"FILE_TOO_LARGE"` and `max_size_bytes` `15728640`.
5. IF an uploaded file has a MIME type outside the accepted list, THEN THE Backend_API SHALL reject the request with HTTP 415 and a JSON error body containing `error_code` `"UNSUPPORTED_MEDIA_TYPE"` and the offending field name.
6. WHEN the contract is a PDF, THE Ingestion_Agent SHALL extract text using Gemini native PDF understanding as the primary path.
7. IF the Gemini PDF extraction call fails or returns empty text, THEN THE Ingestion_Agent SHALL retry extraction using `pdfplumber` and SHALL record the fallback in the Audit Trail Entry for that invocation.
8. THE Ingestion_Agent SHALL detect the contract language as `en` or `vi` and SHALL attach the detected language to each emitted Clause.
9. THE Ingestion_Agent SHALL segment the contract into Clauses, each with a stable `clause_id`, `heading` (nullable), `text`, `language`, and `char_span` indicating the start and end character offsets in the source text.

### Requirement 2: Multi-Agent Pipeline Orchestration

**User Story:** As a backend developer, I want a deterministic six-agent LangGraph pipeline, so that contract analysis is reproducible and observable.

#### Acceptance Criteria

1. WHEN a client sends a `POST /api/analyze` request with a valid `job_id`, THE Backend_API SHALL execute the Agent_Pipeline in the order Ingestion_Agent, Clause_Analysis_Agent, Policy_Mapping_Agent, Risk_Simulation_Agent, Recommendation_Agent, Report_Agent.
2. THE Agent_Pipeline SHALL pass the output of each agent as typed input to the next agent through a LangGraph state object.
3. THE Clause_Analysis_Agent SHALL emit, for every Clause produced by the Ingestion_Agent, a record containing `clause_id`, `clause_type`, `summary`, and `key_terms`.
4. THE Policy_Mapping_Agent SHALL emit, for every Clause, zero or more Violation records each containing `clause_id`, `policy_rule_id`, `risk_category`, `severity`, and `rationale`.
5. THE Risk_Simulation_Agent SHALL evaluate each scenario in `["force_majeure", "penalty_delay", "data_breach", "termination", "payment_default"]` and SHALL emit a record per scenario containing `scenario_key`, `impact_score` between 0 and 100, `affected_clause_ids`, and `narrative`.
6. THE Recommendation_Agent SHALL emit, for every Violation with severity `medium`, `high`, or `critical`, a record containing `clause_id`, `original_text`, `proposed_text`, and `change_rationale`.
7. THE Report_Agent SHALL assemble a Governance Report that includes the Risk Score, the Per-Category Scores, the clause table, the Violations, the simulation results, the recommendations, and the audit trail appendix.
8. WHEN the Agent_Pipeline completes successfully, THE Backend_API SHALL return HTTP 200 with the Governance Report as JSON.
9. IF any agent in the Agent_Pipeline raises an unhandled exception, THEN THE Backend_API SHALL return HTTP 502 with a JSON error body containing `error_code` `"AGENT_FAILURE"`, the failing agent name, and the `job_id`.

### Requirement 3: Dashboard UI

**User Story:** As an executive reviewer, I want a single dashboard summarising the contract analysis, so that I can grasp risk and recommendations at a glance.

#### Acceptance Criteria

1. WHEN a Governance Report is available for a `job_id`, THE Frontend_App SHALL render an Overall Risk Score gauge displaying the integer Risk Score from 0 to 100.
2. THE Frontend_App SHALL render a Risk Heatmap with one row per Risk Category showing the Per-Category Score and a colour band (`green` for 0–33, `amber` for 34–66, `red` for 67–100).
3. THE Frontend_App SHALL render a Key Clauses Summary list showing each Clause's `heading`, `clause_type`, and `summary`.
4. THE Frontend_App SHALL render a Simulation Panel containing one button per What-If Scenario in the MVP scenario set.
5. WHEN a user activates a What-If Scenario button, THE Frontend_App SHALL display the scenario's `impact_score`, `affected_clause_ids`, and `narrative` returned for that `job_id`.
6. THE Frontend_App SHALL render an AI Recommendations section showing each recommendation as a diff between `original_text` and `proposed_text` with the `change_rationale` visible.
7. THE Frontend_App SHALL render an Audit Trail Log section listing each Audit Trail Entry with agent name, timestamp, model version, and latency.
8. WHILE an Analysis Job is in progress, THE Frontend_App SHALL display a per-agent progress indicator naming the currently running agent.
9. THE Frontend_App SHALL provide a "Load Sample Data" control that populates the dashboard from the bundled sample data set without requiring a file upload.

### Requirement 4: Risk Scoring Model

**User Story:** As a governance lead, I want a deterministic, explainable risk score, so that two runs on the same contract produce the same number.

#### Acceptance Criteria

1. THE Backend_API SHALL compute the Per-Category Score for each Risk Category as the sum of severity weights of Violations in that category, capped at 100, where severity weights are `low` = 5, `medium` = 15, `high` = 30, `critical` = 50.
2. THE Backend_API SHALL compute the Risk Score as the rounded weighted mean of the five Per-Category Scores using fixed weights `legal` = 0.25, `financial` = 0.20, `operational` = 0.15, `compliance` = 0.25, `data_privacy` = 0.15.
3. THE Backend_API SHALL include in the Governance Report the Risk Score, the Per-Category Scores, and the input list of Violations used for the computation.
4. WHEN the same Violation list is supplied to the scoring routine on different runs, THE Backend_API SHALL return identical Risk Score and Per-Category Scores values.
5. THE Backend_API SHALL emit Per-Category Score keys using the English Risk Category identifiers regardless of the contract's detected language.

### Requirement 5: Audit Trail and Governance Logging

**User Story:** As a security officer, I want every agent invocation logged with hashes and timing, so that I can audit the system's behaviour after the fact.

#### Acceptance Criteria

1. WHEN any agent in the Agent_Pipeline is invoked, THE Backend_API SHALL persist an Audit Trail Entry containing `job_id`, `agent_name`, `input_sha256`, `output_sha256`, `timestamp_iso8601`, `model_version`, and `latency_ms`.
2. WHEN a client sends `GET /api/audit-trail/{job_id}` for a known `job_id`, THE Backend_API SHALL return HTTP 200 with the ordered list of Audit Trail Entries for that job.
3. IF a `GET /api/audit-trail/{job_id}` request references an unknown `job_id`, THEN THE Backend_API SHALL return HTTP 404 with a JSON error body containing `error_code` `"JOB_NOT_FOUND"`.
4. THE Backend_API SHALL redact email addresses, phone numbers, and government identifier patterns from any free-text fields written to server logs.
5. THE Backend_API SHALL persist Audit Trail Entries to a server-side store that survives a single request lifecycle.
6. THE Frontend_App SHALL display the Audit Trail Entries returned by `GET /api/audit-trail/{job_id}` in chronological order.

### Requirement 6: Prompt-Injection and Output Validation

**User Story:** As a security engineer, I want every agent output validated against a strict schema and every prompt hardened against injection, so that adversarial contract content cannot subvert the pipeline.

#### Acceptance Criteria

1. THE Backend_API SHALL define a Pydantic schema for each agent's output and SHALL validate every Gemini response against the corresponding schema before passing it downstream.
2. IF a Gemini response fails Pydantic validation, THEN THE Backend_API SHALL retry the call exactly once with a repair prompt that includes the original output and the validation error.
3. IF the retry also fails Pydantic validation, THEN THE Backend_API SHALL return HTTP 502 with a JSON error body containing `error_code` `"AGENT_OUTPUT_INVALID"`, the failing agent name, and the validation error message.
4. THE Backend_API SHALL prepend an Anti-Injection Guardrail to every agent system prompt instructing the agent to ignore instructions embedded in user-supplied contract or policy text and to emit only schema-conformant JSON.
5. THE Backend_API SHALL log each validation failure as an Audit Trail Entry with `agent_name` suffixed `:validation_failure`.

### Requirement 7: PDF Report Export

**User Story:** As a partner reviewer, I want to download a polished PDF of the analysis, so that I can share it with stakeholders outside the tool.

#### Acceptance Criteria

1. WHEN a client sends `GET /api/report/{job_id}` for a completed Analysis Job, THE Backend_API SHALL return HTTP 200 with `Content-Type: application/pdf` and a `Content-Disposition: attachment` header carrying a filename of the form `contractforge-report-{job_id}.pdf`.
2. THE Backend_API SHALL generate the PDF server-side and SHALL include, in order, a cover page, an executive summary, a risk score gauge visual, a heatmap table, a clauses table, a violations section, a recommendations section, and an audit trail appendix.
3. IF a `GET /api/report/{job_id}` request references a `job_id` that has not completed analysis, THEN THE Backend_API SHALL return HTTP 409 with a JSON error body containing `error_code` `"REPORT_NOT_READY"`.
4. THE Frontend_App SHALL provide a "Download PDF Report" control on the dashboard that triggers `GET /api/report/{job_id}` for the current `job_id`.

### Requirement 8: REST API Surface

**User Story:** As a frontend developer, I want a documented set of REST endpoints, so that I can integrate the dashboard reliably.

#### Acceptance Criteria

1. THE Backend_API SHALL expose `POST /api/upload` accepting `multipart/form-data` with `contract` and `policy` parts.
2. THE Backend_API SHALL expose `POST /api/analyze` accepting a JSON body with a `job_id` string.
3. THE Backend_API SHALL expose `POST /api/simulate` accepting a JSON body with `job_id` and `scenario_key` and returning the simulation result for that scenario.
4. THE Backend_API SHALL expose `GET /api/report/{job_id}` returning the PDF Governance Report.
5. THE Backend_API SHALL expose `GET /api/audit-trail/{job_id}` returning the JSON list of Audit Trail Entries.
6. THE Backend_API SHALL expose `GET /api/health` returning HTTP 200 with a JSON body containing `status` `"ok"`, `version`, and `gemini_configured` boolean.
7. IF a `POST /api/simulate` request references a `scenario_key` outside the MVP What-If Scenario set, THEN THE Backend_API SHALL return HTTP 400 with `error_code` `"UNKNOWN_SCENARIO"`.

### Requirement 9: Bilingual Behavior

**User Story:** As a Vietnamese-speaking analyst, I want the system to respond in the contract's language while keeping risk taxonomy stable, so that I can read the analysis natively without breaking the scoring model.

#### Acceptance Criteria

1. THE Ingestion_Agent SHALL detect the contract language as either `en` or `vi` and SHALL include the detected language on every Clause.
2. WHEN the detected contract language is `vi`, THE Clause_Analysis_Agent SHALL emit `summary` and `key_terms` in Vietnamese.
3. WHEN the detected contract language is `en`, THE Clause_Analysis_Agent SHALL emit `summary` and `key_terms` in English.
4. WHEN the detected contract language is `vi`, THE Recommendation_Agent SHALL emit `proposed_text` and `change_rationale` in Vietnamese.
5. THE Backend_API SHALL emit Risk Category identifiers, severity identifiers, and What-If Scenario keys in English regardless of the detected contract language.

### Requirement 10: Deployment Readiness

**User Story:** As a DevOps engineer, I want one-command deploy artefacts, so that the demo runs reliably on Vercel and Render or Fly.io.

#### Acceptance Criteria

1. THE Auditor_System SHALL include a `Dockerfile` at the backend project root that builds a runnable FastAPI image.
2. THE Auditor_System SHALL include a `render.yaml` or `fly.toml` describing the backend service.
3. THE Auditor_System SHALL include a `vercel.json` and a `.env.example` for the frontend specifying `VITE_API_BASE_URL`.
4. THE Backend_API SHALL enable CORS for the configured frontend origin via an environment variable `FRONTEND_ORIGIN`.
5. WHEN the Backend_API process starts, THE Backend_API SHALL read the `GOOGLE_API_KEY` environment variable.
6. IF `GOOGLE_API_KEY` is missing or empty at startup, THEN THE Backend_API SHALL exit with a non-zero status code and a stderr message containing `GOOGLE_API_KEY is required`.
7. THE Auditor_System SHALL include a backend `.env.example` listing `GOOGLE_API_KEY`, `FRONTEND_ORIGIN`, and `GEMINI_MODEL`.

### Requirement 11: Demo Quality and UX

**User Story:** As a hackathon judge, I want a polished, responsive UI with clear progress and error states, so that the demo feels production-grade.

#### Acceptance Criteria

1. THE Frontend_App SHALL be built with React 18, Vite, TypeScript, TailwindCSS, shadcn/ui, and Zustand.
2. THE Frontend_App SHALL render correctly on viewport widths from 360 pixels through 1920 pixels.
3. WHILE an Analysis Job is in progress, THE Frontend_App SHALL display a non-blocking progress indicator naming the currently running agent and SHALL update at least once every 2 seconds via polling or streaming.
4. IF the Backend_API returns an HTTP 4xx or 5xx response, THEN THE Frontend_App SHALL display the `error_code` and a human-readable message in a dismissible toast.
5. THE Frontend_App SHALL include a "Load Sample Data" control that runs an end-to-end analysis using the bundled sample data without requiring a file upload.
6. THE Frontend_App SHALL show a skeleton or shimmer placeholder for each dashboard section while its data is loading.

### Requirement 12: Sample Data

**User Story:** As a presenter, I want bundled bilingual sample data, so that I can demo the system without uploading anything live.

#### Acceptance Criteria

1. THE Auditor_System SHALL include at least one English sample contract representative of a SaaS Master Services Agreement.
2. THE Auditor_System SHALL include at least one Vietnamese sample contract representative of a service agreement (`hợp đồng dịch vụ`).
3. THE Auditor_System SHALL include at least one sample policy file covering policy rules referenced by both sample contracts, in either a bilingual single file or paired English and Vietnamese files.
4. WHEN the Frontend_App "Load Sample Data" control is activated, THE Auditor_System SHALL run the full Agent_Pipeline against the bundled sample contract and sample policy and SHALL render the resulting Governance Report on the dashboard.
