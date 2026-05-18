"""
Governance & Recommendation Agent for ContractForge Auditor.

Proposes amended clause text for every violation whose severity is
``medium``, ``high``, or ``critical``.  Calls the Gemini API via
``gemini_client.invoke`` and returns a partial-state dict containing
``recommendations``.

References
----------
- Req 2.6  — Redline recommendations for non-compliant clauses.
- Req 9.4  — Recommendation Agent prompt and output schema.
- Req 9.5  — ``proposed_text`` and ``change_rationale`` written in the
             contract language.
"""

from __future__ import annotations

import json

from app.agents import gemini_client
from app.agents.prompts import RECOMMENDATION_PROMPT
from app.agents.schemas import RecommendationList
from app.agents.state import PipelineState


def run(state: PipelineState) -> dict:
    """Execute the Governance & Recommendation Agent.

    Reads ``clauses``, ``violations``, ``language``, and ``job_id`` from
    *state*, formats the ``RECOMMENDATION_PROMPT``, calls Gemini, and returns
    a partial-state dict containing ``recommendations``.

    Only violations with severity ``"medium"``, ``"high"``, or ``"critical"``
    receive a recommendation; ``"low"`` violations are skipped by the prompt
    instruction.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  Must contain:
        - ``clauses``    — list of clause dicts from the ingestion agent.
        - ``language``   — ``"en"`` or ``"vi"``.
        - ``job_id``     — UUID v4 identifying the current analysis job.
        - ``violations`` — list of violation dicts from the policy-mapping
                           agent; may be absent or empty.

    Returns
    -------
    dict
        ``{"recommendations": [<Recommendation as dict>, ...]}``

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so the pipeline can handle it at the orchestration layer.
    """
    clauses: list[dict] = state["clauses"]
    violations: list[dict] = state.get("violations", []) or []
    language: str = state["language"]
    job_id: str = state["job_id"]

    prompt = RECOMMENDATION_PROMPT.format(
        language=language,
        clauses_json=json.dumps(clauses, ensure_ascii=False),
        violations_json=json.dumps(violations, ensure_ascii=False),
    )

    result: RecommendationList = gemini_client.invoke(
        prompt,
        RecommendationList,
        "recommendation",
        job_id,
    )

    return {"recommendations": [r.model_dump() for r in result.recommendations]}
