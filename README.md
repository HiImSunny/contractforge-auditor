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

See [`backend/.env.example`](backend/.env.example) for a template.

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | Base URL of the backend API, no trailing slash |

See [`frontend/.env.example`](frontend/.env.example) for a template.

---

## Spec Files

- [Requirements](.kiro/specs/contractforge-auditor/requirements.md)
- [Design](.kiro/specs/contractforge-auditor/design.md)
- [Tasks](.kiro/specs/contractforge-auditor/tasks.md)

---

## Hackathon Tracks

This project is submitted to two tracks:

**Agent Security & AI Governance** — Every Gemini call is logged in an auditable trail with SHA-256 input/output hashes, ISO timestamps, model version, and latency. All agent outputs are validated against strict Pydantic v2 schemas with a single repair retry. Anti-injection guardrails are prepended to every system prompt. PII (email, phone, government IDs) is regex-redacted before any free-text field touches a log line.

**Gemini Agents** — Six specialised Gemini agents are orchestrated through LangGraph: Ingestion & Extraction, Clause Analysis, Policy Compliance & Mapping, Risk Simulation, Governance & Recommendation, and Report Generation. The pipeline exercises Gemini's native PDF understanding, structured JSON output, and bilingual EN/VI reasoning.

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
