"""
Ingestion & Extraction Agent for ContractForge Auditor.

This module implements the first stage of the LangGraph pipeline.  It reads
plain contract text from ``PipelineState``, falls back to a ``pdf_parser``
shim when the text is absent, formats the ``INGESTION_PROMPT``, and calls
``gemini_client.invoke`` to segment the contract into typed ``Clause`` objects.

References
----------
- Req 1.6  — Gemini native PDF understanding as the primary extraction path.
- Req 1.7  — Fallback to ``pdfplumber`` (via ``pdf_parser.extract_text``) when
             the primary path returns empty text.
- Req 1.8  — Each emitted ``Clause`` carries a stable ``clause_id``, nullable
             ``heading``, verbatim ``text``, ``language``, and ``char_span``.
- Req 1.9  — The agent detects the contract language as ``"en"`` or ``"vi"``
             and attaches it to every ``Clause``.
- Req 9.1  — Language detection is surfaced on the top-level ``language`` key
             of the returned partial state dict.
"""

from __future__ import annotations

from app.agents import gemini_client
from app.agents.prompts import INGESTION_PROMPT
from app.agents.schemas import ClauseList
from app.agents.state import PipelineState


def run(state: PipelineState) -> dict:
    """Execute the Ingestion & Extraction Agent.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  The agent reads
        ``state["contract_text"]`` (plain text) and ``state["job_id"]``.

    Returns
    -------
    dict
        A partial state dict with two keys:

        ``clauses``
            A list of plain dicts (one per extracted clause), each matching
            the ``Clause`` Pydantic schema serialised via ``model_dump()``.
        ``language``
            The dominant language detected for the contract (``"en"`` or
            ``"vi"``).

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so that the route handler in Task 4.4 can catch it and
        return HTTP 502 ``AGENT_FAILURE``.
    """
    job_id: str = state.get("job_id", "")
    contract_text: str = state.get("contract_text", "") or ""

    # ── Fallback: try pdf_parser shim when contract_text is empty ────────────
    if not contract_text:
        try:
            from app.services.pdf_parser import extract_text  # type: ignore[import]

            contract_text = extract_text(state.get("contract_bytes", b""))
        except ImportError:
            contract_text = ""

    # ── Build prompt ─────────────────────────────────────────────────────────
    prompt = INGESTION_PROMPT.format(contract_text=contract_text)

    # ── Call Gemini (exceptions propagate to the caller) ─────────────────────
    result: ClauseList = gemini_client.invoke(
        prompt,
        ClauseList,
        "ingestion",
        job_id,
    )

    return {
        "clauses": [c.model_dump() for c in result.clauses],
        "language": result.language,
    }
