"""
LangGraph pipeline state for ContractForge Auditor.

``PipelineState`` is the single shared object passed through every node in the
LangGraph pipeline (Req 2.2).  Each agent node receives the full state, reads
the keys it needs, and returns a partial-state dict that LangGraph merges back
in before invoking the next node.

Design note — plain dicts instead of Pydantic models
-----------------------------------------------------
The list fields (``clauses``, ``clause_analyses``, ``violations``,
``simulations``, ``recommendations``, ``audit_entries``) carry plain
``dict`` values rather than the typed Pydantic models defined in
``schemas.py``.  This avoids two problems:

1. **Circular imports** — ``state.py`` is imported by ``graph.py`` and by
   every agent module; importing ``schemas.py`` and ``audit_log.py`` here
   would create an import cycle.
2. **LangGraph serialisation** — LangGraph checkpoints state via JSON; plain
   dicts round-trip cleanly, whereas Pydantic model instances require a
   custom serialiser.

Validation against the Pydantic models in ``schemas.py`` is performed at the
agent boundary inside ``gemini_client.invoke``, so type safety is preserved
where it matters.
"""

from typing import Literal, Optional, TypedDict

Language = Literal["en", "vi"]


class PipelineState(TypedDict, total=False):
    job_id: str
    contract_text: str
    policy_text: str
    language: Language
    clauses: list[dict]          # list[Clause] as dicts for LangGraph serialisation
    clause_analyses: list[dict]  # list[ClauseAnalysis] as dicts
    violations: list[dict]       # list[Violation] as dicts
    simulations: list[dict]      # list[SimulationResult] as dicts
    recommendations: list[dict]  # list[Recommendation] as dicts
    report: Optional[dict]       # GovernanceReport as dict
    audit_entries: list[dict]    # list[AuditEntry] as dicts
