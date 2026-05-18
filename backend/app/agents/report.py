"""
Report Generation Agent for ContractForge Auditor.

Generates the narrative portion of the Governance Report (headline,
executive summary, top risks) by calling the Gemini API via
``gemini_client.invoke``.  Deterministic risk scores are computed locally
via ``services.risk_scoring.score`` and merged into the returned dict so
the route handler receives a complete, ready-to-serialise report.

References
----------
- Req 2.7  — Governance Report generation combining AI narrative with
             deterministic scoring.
- Req 4.1  — Per-category risk scores computed from violations.
- Req 4.2  — Overall risk score as a weighted mean of per-category scores.
- Req 9.5  — ``headline`` and ``executive_summary`` written in the contract
             language.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from app.agents import gemini_client
from app.agents.prompts import REPORT_PROMPT
from app.agents.state import PipelineState
from app.services.risk_scoring import score as compute_score


# ---------------------------------------------------------------------------
# Local schema — only used by this agent
# ---------------------------------------------------------------------------


class ReportNarrative(BaseModel):
    """Gemini-generated narrative portion of the Governance Report.

    The deterministic fields (risk scores, clause table, violations,
    simulations, recommendations, audit trail) are computed by other
    components and merged in by ``run``; Gemini only produces the three
    narrative fields below.
    """

    headline: str = Field(max_length=120)
    """One-line summary of the overall audit outcome (≤ 120 chars)."""

    executive_summary: str
    """3–6 sentence executive summary written in the contract language."""

    top_risks: list[str] = Field(min_length=3, max_length=5)
    """3–5 short bullet phrases describing the most significant risks."""


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------


def run(state: PipelineState) -> dict:
    """Execute the Report Generation Agent.

    Reads ``violations``, ``language``, and ``job_id`` from *state*,
    computes deterministic risk scores, formats the ``REPORT_PROMPT``,
    calls Gemini for the narrative fields, and returns a partial-state dict
    containing a complete ``report`` dict.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  Must contain:
        - ``language``        — ``"en"`` or ``"vi"``.
        - ``job_id``          — UUID v4 identifying the current analysis job.
        - ``violations``      — list of violation dicts; may be absent or empty.
        - ``clauses``         — list of clause dicts; may be absent or empty.
        - ``clause_analyses`` — list of clause-analysis dicts; may be absent.
        - ``simulations``     — list of simulation-result dicts; may be absent.
        - ``recommendations`` — list of recommendation dicts; may be absent.
        - ``audit_entries``   — list of audit-entry dicts; may be absent.

    Returns
    -------
    dict
        ``{"report": <GovernanceReport as dict>}``

        The ``report`` dict contains all fields required by the
        ``GovernanceReport`` Pydantic schema, including the Gemini-generated
        narrative fields and the deterministic risk scores.

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so the pipeline can handle it at the orchestration layer.
    """
    violations: list[dict] = state.get("violations", []) or []
    language: str = state["language"]
    job_id: str = state["job_id"]

    # Compute deterministic scores from violations (Req 4.1, 4.2).
    per_category, overall = compute_score(violations)

    # Build a compact violations summary for the prompt to keep token usage
    # low — the full violation list is already stored in state.
    violations_summary = _summarise_violations(violations)

    prompt = REPORT_PROMPT.format(
        language=language,
        risk_score=overall,
        per_category_scores_json=json.dumps(per_category, ensure_ascii=False),
        violations_summary_json=json.dumps(violations_summary, ensure_ascii=False),
    )

    result: ReportNarrative = gemini_client.invoke(
        prompt,
        ReportNarrative,
        "report_gen",
        job_id,
    )

    return {
        "report": {
            "job_id": job_id,
            "language": language,
            "headline": result.headline,
            "executive_summary": result.executive_summary,
            "top_risks": result.top_risks,
            "risk_score": overall,
            "per_category_scores": per_category,
            "clauses": state.get("clauses", []) or [],
            "clause_analyses": state.get("clause_analyses", []) or [],
            "violations": violations,
            "simulations": state.get("simulations", []) or [],
            "recommendations": state.get("recommendations", []) or [],
            "audit_trail": state.get("audit_entries", []) or [],
        }
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _summarise_violations(violations: list[dict]) -> list[dict]:
    """Return a compact summary of violations for the report prompt.

    Strips verbose fields (``rationale``, ``policy_rule_id``) to keep the
    prompt concise while still giving the model enough context to write an
    accurate executive summary.

    Parameters
    ----------
    violations:
        Full violation dicts as stored in ``PipelineState``.

    Returns
    -------
    list[dict]
        Each dict contains only ``clause_id``, ``risk_category``, and
        ``severity``.
    """
    return [
        {
            "clause_id": v.get("clause_id"),
            "risk_category": v.get("risk_category"),
            "severity": v.get("severity"),
        }
        for v in violations
    ]
