"""
Clause Analysis Agent for ContractForge Auditor.

Classifies and summarises each extracted contract clause by calling the
Gemini API via ``gemini_client.invoke``.

References:
  - Req 2.3  — Clause classification using the fixed English taxonomy.
  - Req 9.2  — Clause Analysis Agent prompt and output schema.
  - Req 9.3  — Summary and key_terms written in the contract language.
"""

from __future__ import annotations

import json

from app.agents import gemini_client
from app.agents.prompts import CLAUSE_ANALYSIS_PROMPT
from app.agents.schemas import ClauseAnalysisList
from app.agents.state import PipelineState


def run(state: PipelineState) -> dict:
    """Execute the Clause Analysis Agent.

    Reads ``clauses``, ``language``, and ``job_id`` from *state*, formats
    the ``CLAUSE_ANALYSIS_PROMPT``, calls Gemini, and returns a partial-state
    dict containing ``clause_analyses``.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  Must contain:
        - ``clauses``  — list of clause dicts produced by the ingestion agent.
        - ``language`` — ``"en"`` or ``"vi"``.
        - ``job_id``   — UUID v4 identifying the current analysis job.

    Returns
    -------
    dict
        ``{"clause_analyses": [<ClauseAnalysis as dict>, ...]}``

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so the pipeline can handle it at the orchestration layer.
    """
    clauses: list[dict] = state["clauses"]
    language: str = state["language"]
    job_id: str = state["job_id"]

    clauses_json = json.dumps(clauses, ensure_ascii=False)

    prompt = CLAUSE_ANALYSIS_PROMPT.format(
        language=language,
        clauses_json=clauses_json,
    )

    result: ClauseAnalysisList = gemini_client.invoke(
        prompt,
        ClauseAnalysisList,
        "clause_analysis",
        job_id,
    )

    return {"clause_analyses": [a.model_dump() for a in result.analyses]}
