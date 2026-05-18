# ContractForge Auditor

A multi-agent AI platform for enterprise contract governance — upload a contract and a policy file, and get a structured risk report powered by a six-stage LangGraph pipeline running on Google Gemini.

![Agent Security & AI Governance](https://img.shields.io/badge/Track-Agent%20Security%20%26%20AI%20Governance-blue)
![Gemini Agents](https://img.shields.io/badge/Track-Gemini%20Agents-orange)

---

## Project Layout

```
contractforge-auditor/
├── backend/    # FastAPI + LangGraph agent pipeline (Python)
└── frontend/   # React 18 + Vite + TypeScript dashboard (Node)
```

- **backend/** — FastAPI service exposing `/api/*` endpoints, the six-agent LangGraph pipeline, risk scoring, PDF export, and audit trail logging.
- **frontend/** — Single-page React dashboard with risk gauge, heatmap, simulation panel, recommendations diff, and audit trail viewer.

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com/) API key

### Backend

```bash
cd backend

# Copy and fill in environment variables
cp .env.example .env
# Edit .env — set GOOGLE_API_KEY and FRONTEND_ORIGIN

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend

# Copy and fill in environment variables
cp .env.example .env.local
# Edit .env.local — set VITE_API_BASE_URL=http://localhost:8000

# Install dependencies
npm install

# Start the development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Google AI Studio API key for Gemini |
| `FRONTEND_ORIGIN` | Yes | Comma-separated allowed CORS origins (e.g. `http://localhost:5173`) |
| `GEMINI_MODEL` | No | Gemini model name (defaults to `gemini-1.5-flash`) |
| `LOBSTERTRAP_URL` | No | Lobster Trap DPI proxy URL (e.g. `http://localhost:8080`). When set, all Gemini calls are routed through the proxy. Leave empty to call Gemini directly. |

See [`backend/.env.example`](backend/.env.example) for a template.

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | Base URL of the backend API, no trailing slash |

See [`frontend/.env.example`](frontend/.env.example) for a template.

---

## Lobster Trap — Deep Prompt Inspection (Veea)

ContractForge Auditor integrates [Lobster Trap](https://github.com/veea-ai/lobstertrap) (MIT), a DPI proxy by Veea that sits between the agent pipeline and the Gemini API, enforcing P4-style firewall rules on every prompt and response.

```
ContractForge Agents → Lobster Trap Proxy → Gemini API
                              ↓
                    Policy enforcement
                    Prompt injection detection
                    PII exfiltration prevention
                    Credential leak blocking
                    Governance audit trail
```

### Policy Pack

The policy file at [`configs/lobstertrap_policy.yaml`](configs/lobstertrap_policy.yaml) defines 9 rules tailored for legal contract governance:

| Rule ID | Name | Action |
|---|---|---|
| CF-SEC-001 | Block credential exfiltration | DENY |
| CF-SEC-002 | Detect prompt injection in contract content | QUARANTINE |
| CF-SEC-003 | Detect PII in agent responses | HUMAN_REVIEW |
| CF-SEC-004 | Block data exfiltration via external domains | DENY |
| CF-GOV-001 | Intent mismatch detection | LOG |
| CF-SEC-005 | Block risky command execution patterns | DENY |
| CF-RATE-001 | Rate limit ingestion agent calls | RATE_LIMIT |
| CF-GOV-002 | Log schema drift in agent responses | LOG |
| CF-ALLOW-001 | Allow legitimate agent pipeline traffic | ALLOW |

### Running with Lobster Trap (Docker Compose)

```bash
# Copy and fill in environment variables
cp backend/.env.example backend/.env
# Edit backend/.env — set GOOGLE_API_KEY

# Start both backend and Lobster Trap proxy
docker compose up --build

# Backend API:        http://localhost:8000
# Lobster Trap proxy: http://localhost:8080
# Dashboard UI:       http://localhost:8081
```

The `LOBSTERTRAP_URL=http://lobstertrap:8080` env var is set automatically in `docker-compose.yml`. All Gemini calls from the backend are routed through the proxy.

### Running without Lobster Trap

Leave `LOBSTERTRAP_URL` empty (or unset) in your `.env`. The backend calls Gemini directly. Application-level guardrails (GUARDRAIL prompt prefix, Pydantic validation, PII redaction, audit log) remain active.

---

## Spec Files

- [Requirements](.kiro/specs/contractforge-auditor/requirements.md)
- [Design](.kiro/specs/contractforge-auditor/design.md)
- [Tasks](.kiro/specs/contractforge-auditor/tasks.md)

---

## Hackathon Tracks

This project is submitted to two tracks:

**Agent Security & AI Governance (Track 1 — powered by Veea)** — Every Gemini call passes through [Lobster Trap](https://github.com/veea-ai/lobstertrap), Veea's DPI proxy, which enforces 9 custom policy rules: blocking credential exfiltration, quarantining prompt injection attempts, flagging PII in responses, detecting declared-vs-detected intent mismatches, and rate-limiting the ingestion agent. On top of the network layer, every call is logged in an auditable trail with SHA-256 input/output hashes, ISO timestamps, model version, and latency. All agent outputs are validated against strict Pydantic v2 schemas with a single repair retry. Anti-injection guardrails are prepended to every system prompt. PII (email, phone, government IDs) is regex-redacted before any free-text field touches a log line.

**Gemini Agents (Track 2)** — Six specialised Gemini agents are orchestrated through LangGraph: Ingestion & Extraction, Clause Analysis, Policy Compliance & Mapping, Risk Simulation, Governance & Recommendation, and Report Generation. The pipeline exercises Gemini's native PDF understanding, structured JSON output, and bilingual EN/VI reasoning.

---

## Demo Backup Procedure

If the live demo environment is unavailable, follow these steps to record a backup screen capture:

1. Start the backend locally: `cd backend && GOOGLE_API_KEY=your_key uvicorn app.main:app --reload`
2. Start the frontend locally: `cd frontend && npm run dev`
3. Open `http://localhost:5173` in a browser
4. Start a screen recording (90 seconds target)
5. Click **Load Sample Data** — watch the 6-agent pipeline progress strip
6. When the dashboard loads, point out the **Risk Score gauge** and **Risk Heatmap**
7. Click **Force Majeure** in the What-If Simulation panel — show the impact score and narrative
8. Click **Data Breach** — show the high impact score
9. Scroll to **Recommendations** — show the side-by-side diff
10. Scroll to **Audit Trail** — show the SHA-256 hashes and latency
11. Click **Download PDF Report** — show the downloaded file
12. End recording with the closing pitch: "Six Gemini agents, hardened prompts, full audit trail — that's ContractForge Auditor."

Save the recording as `demo-backup.mp4` in the project root (gitignored).
