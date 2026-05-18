"""
End-to-end integration test for the load-sample → analyze flow.

Validates: Requirements 12.4, 2.8
"""
import json
import os
import pytest

# Set required env vars before importing the app
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")
os.environ.setdefault("GEMINI_MODEL", "gemini-1.5-flash")

from unittest.mock import patch
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Canned responses for each agent
# ---------------------------------------------------------------------------

CANNED_INGESTION = json.dumps({
    "language": "en",
    "clauses": [
        {
            "clause_id": "C-001",
            "heading": "1. Term",
            "text": "This Agreement commences on the Effective Date.",
            "language": "en",
            "char_span": {"start": 0, "end": 47}
        }
    ]
})

CANNED_CLAUSE_ANALYSIS = json.dumps({
    "analyses": [
        {
            "clause_id": "C-001",
            "clause_type": "term",
            "summary": "The agreement starts on the effective date.",
            "key_terms": ["effective date", "commencement"]
        }
    ]
})

CANNED_POLICY_MAPPING = json.dumps({
    "violations": [
        {
            "clause_id": "C-001",
            "policy_rule_id": "POL-LG-001",
            "risk_category": "legal",
            "severity": "high",
            "rationale": "Liability cap is below the required 12-month threshold."
        }
    ]
})

CANNED_RISK_SIMULATION = json.dumps({
    "simulations": [
        {
            "scenario_key": "force_majeure",
            "impact_score": 60,
            "affected_clause_ids": ["C-001"],
            "narrative": "Force majeure could suspend performance."
        },
        {
            "scenario_key": "penalty_delay",
            "impact_score": 40,
            "affected_clause_ids": ["C-001"],
            "narrative": "Delay triggers penalties."
        },
        {
            "scenario_key": "data_breach",
            "impact_score": 80,
            "affected_clause_ids": ["C-001"],
            "narrative": "Data breach exposure is high."
        },
        {
            "scenario_key": "termination",
            "impact_score": 30,
            "affected_clause_ids": ["C-001"],
            "narrative": "Termination requires 30-day notice."
        },
        {
            "scenario_key": "payment_default",
            "impact_score": 50,
            "affected_clause_ids": ["C-001"],
            "narrative": "Payment default after 60 days."
        },
    ]
})

CANNED_RECOMMENDATION = json.dumps({
    "recommendations": [
        {
            "clause_id": "C-001",
            "original_text": "This Agreement commences on the Effective Date.",
            "proposed_text": "This Agreement commences on the Effective Date, with liability capped at 12 months of fees.",
            "change_rationale": "Aligns with POL-LG-001 requiring a 12-month liability cap."
        }
    ]
})

CANNED_REPORT = json.dumps({
    "headline": "High legal exposure in a standard SaaS MSA.",
    "executive_summary": "The contract scores 30/100 overall. One critical legal violation requires amendment.",
    "top_risks": ["Liability cap below policy floor", "Termination clause ambiguity", "Data handling gaps"]
})


def _make_mock_call_gemini():
    """
    Return a mock for ``_call_gemini`` that routes based on unique keywords
    present in each agent's formatted prompt.

    Routing heuristics (each keyword is unique to one prompt template):
      - ``RISK_SCORE``          → report agent (REPORT_PROMPT)
      - ``SCENARIOS``           → risk simulation agent (RISK_SIMULATION_PROMPT)
      - ``POLICY_RULES``        → policy mapping agent (POLICY_MAPPING_PROMPT)
      - ``VIOLATIONS``          → recommendation agent (RECOMMENDATION_PROMPT)
      - ``CLAUSE_ANALYSIS``     → clause analysis agent (CLAUSE_ANALYSIS_PROMPT)
      - fallback                → ingestion agent (INGESTION_PROMPT)
    """
    def mock_call_gemini(prompt: str) -> str:
        # REPORT_PROMPT contains "RISK_SCORE:" as a template placeholder label
        if "RISK_SCORE:" in prompt:
            return CANNED_REPORT
        # RISK_SIMULATION_PROMPT contains "SCENARIOS" in its body
        if "SCENARIOS" in prompt:
            return CANNED_RISK_SIMULATION
        # POLICY_MAPPING_PROMPT contains "POLICY_RULES:" as a label
        if "POLICY_RULES:" in prompt:
            return CANNED_POLICY_MAPPING
        # RECOMMENDATION_PROMPT contains "VIOLATIONS:" as a label
        if "VIOLATIONS:" in prompt:
            return CANNED_RECOMMENDATION
        # CLAUSE_ANALYSIS_PROMPT contains "Clause Analysis Agent" in its ROLE line
        if "Clause Analysis Agent" in prompt:
            return CANNED_CLAUSE_ANALYSIS
        # Default: ingestion agent
        return CANNED_INGESTION

    return mock_call_gemini


# ---------------------------------------------------------------------------
# E2E test
# ---------------------------------------------------------------------------

def test_load_sample_then_analyze():
    """E2E: load-sample → analyze returns a complete GovernanceReport with audit trail.

    **Validates: Requirements 12.4, 2.8**
    """
    from app.main import app

    with patch("app.agents.gemini_client._call_gemini", side_effect=_make_mock_call_gemini()):
        client = TestClient(app)

        # ── Step 1: Load sample ──────────────────────────────────────────────
        resp = client.post("/api/load-sample")
        assert resp.status_code == 200, f"load-sample failed: {resp.text}"
        data = resp.json()
        assert "job_id" in data, "Response must contain job_id"
        job_id = data["job_id"]
        assert data["detected_language"] == "en", "Sample contract should be detected as English"

        # ── Step 2: Analyze ──────────────────────────────────────────────────
        resp = client.post("/api/analyze", json={"job_id": job_id})
        assert resp.status_code == 200, f"analyze failed: {resp.text}"
        report = resp.json()

        # Assert GovernanceReport top-level structure
        assert "job_id" in report, "Report must contain job_id"
        assert report["job_id"] == job_id, "Report job_id must match the submitted job_id"

        assert "risk_score" in report, "Report must contain risk_score"
        assert isinstance(report["risk_score"], int), "risk_score must be an integer"
        assert 0 <= report["risk_score"] <= 100, "risk_score must be in [0, 100]"

        assert "per_category_scores" in report, "Report must contain per_category_scores"
        per_cat = report["per_category_scores"]
        for category in ("legal", "financial", "operational", "compliance", "data_privacy"):
            assert category in per_cat, f"per_category_scores must contain '{category}'"
            assert 0 <= per_cat[category] <= 100, f"{category} score must be in [0, 100]"

        assert "clauses" in report, "Report must contain clauses"
        assert len(report["clauses"]) > 0, "Report must have at least one clause"

        assert "clause_analyses" in report, "Report must contain clause_analyses"

        assert "violations" in report, "Report must contain violations"

        assert "simulations" in report, "Report must contain simulations"
        assert len(report["simulations"]) == 5, "Report must contain exactly 5 simulation results"

        assert "recommendations" in report, "Report must contain recommendations"

        assert "audit_trail" in report, "Report must contain audit_trail"

        assert "headline" in report, "Report must contain headline"
        assert "executive_summary" in report, "Report must contain executive_summary"
        assert "top_risks" in report, "Report must contain top_risks"

        # ── Step 3: Check audit trail via dedicated endpoint ─────────────────
        resp = client.get(f"/api/audit-trail/{job_id}")
        assert resp.status_code == 200, f"audit-trail endpoint failed: {resp.text}"
        trail = resp.json()
        assert len(trail) > 0, "Audit trail should be non-empty after analysis"

        # Each audit entry should have the required fields
        for entry in trail:
            assert "agent_name" in entry, "Audit entry must have agent_name"
            assert "timestamp_iso8601" in entry, "Audit entry must have timestamp_iso8601"
            assert "input_sha256" in entry, "Audit entry must have input_sha256"
            assert "output_sha256" in entry, "Audit entry must have output_sha256"
            assert len(entry["input_sha256"]) == 64, "input_sha256 must be 64 hex chars"
            assert len(entry["output_sha256"]) == 64, "output_sha256 must be 64 hex chars"
