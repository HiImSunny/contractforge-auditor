"""
Single source of truth for all agent output schemas (Req 6.1).

Every Pydantic v2 model in this module corresponds to a structured JSON
response that one of the LangGraph agents is expected to produce.  The
models are used both for response validation inside ``gemini_client.invoke``
and as the ``response_schema`` hint passed to the Gemini API.

Models are grouped by pipeline stage:

* **Ingestion & Extraction** — ``CharSpan``, ``Clause``, ``ClauseList``
* **Clause Analysis** — ``ClauseAnalysis``, ``ClauseAnalysisList``

Additional models for later pipeline stages (Policy Mapping, Risk
Simulation, Recommendation, Report) are added in task 3.2.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared literal types
# ---------------------------------------------------------------------------

Language = Literal["en", "vi"]
"""Supported contract languages (ISO 639-1 codes)."""

ClauseType = Literal[
    "term",
    "termination",
    "payment",
    "confidentiality",
    "data_protection",
    "liability",
    "indemnification",
    "force_majeure",
    "governing_law",
    "ip_assignment",
    "warranty",
    "service_level",
    "compliance",
    "other",
]
"""Fixed English taxonomy of clause types (Req 2.3).

Values are intentionally kept in English regardless of the contract
language so that downstream policy-mapping logic can use stable keys.
"""

# ---------------------------------------------------------------------------
# Ingestion & Extraction schemas
# ---------------------------------------------------------------------------


class CharSpan(BaseModel):
    """Character-level byte span within the original contract text."""

    start: Annotated[int, Field(ge=0)]
    """Inclusive start offset (≥ 0)."""

    end: Annotated[int, Field(ge=1)]
    """Exclusive end offset (≥ 1, must be > start — enforced by the agent prompt)."""


class Clause(BaseModel):
    """A single extracted contract clause (Req 1.8)."""

    clause_id: str = Field(min_length=1, max_length=32)
    """Stable identifier, e.g. ``"C-001"``.  Must be unique within a ``ClauseList``."""

    heading: Optional[str] = None
    """Section heading if present in the source text, otherwise ``None``."""

    text: str = Field(min_length=1)
    """Verbatim clause body copied from the contract text — never paraphrased."""

    language: Language
    """Detected dominant language of the contract (Req 1.9)."""

    char_span: CharSpan
    """Offsets into the original contract text such that ``text[start:end] == text``."""


class ClauseList(BaseModel):
    """Output schema for the Ingestion & Extraction Agent."""

    language: Language
    """Dominant language detected for the whole contract."""

    clauses: list[Clause]
    """Ordered list of extracted clauses; may be empty for blank contracts."""


# ---------------------------------------------------------------------------
# Clause Analysis schemas
# ---------------------------------------------------------------------------


class ClauseAnalysis(BaseModel):
    """Classification and summary for a single clause (Req 2.3)."""

    clause_id: str
    """Must match a ``clause_id`` from the corresponding ``ClauseList``."""

    clause_type: ClauseType
    """Clause category drawn from the fixed English taxonomy."""

    summary: str = Field(min_length=1)
    """One-to-three sentence summary written in the contract language."""

    key_terms: list[str] = Field(default_factory=list, max_length=10)
    """Up to ten short key phrases extracted from the clause, in the contract language."""


class ClauseAnalysisList(BaseModel):
    """Output schema for the Clause Analysis Agent."""

    analyses: list[ClauseAnalysis]
    """One ``ClauseAnalysis`` per input clause, in the same order."""


# ---------------------------------------------------------------------------
# Shared literal types (additional)
# ---------------------------------------------------------------------------

RiskCategory = Literal["legal", "financial", "operational", "compliance", "data_privacy"]
"""Fixed English risk category keys used across Policy Mapping and Governance Report."""

Severity = Literal["low", "medium", "high", "critical"]
"""Ordered severity levels for policy violations (Req 2.4)."""

ScenarioKey = Literal[
    "force_majeure",
    "penalty_delay",
    "data_breach",
    "termination",
    "payment_default",
]
"""Fixed set of risk simulation scenario identifiers (Req 2.6)."""

# ---------------------------------------------------------------------------
# Policy Compliance & Mapping schemas
# ---------------------------------------------------------------------------


class Violation(BaseModel):
    """A single policy rule violation detected in a contract clause (Req 2.4, 2.5)."""

    clause_id: str
    """Must match a ``clause_id`` from the corresponding ``ClauseList``."""

    policy_rule_id: str
    """Verbatim rule identifier copied from the policy document — never invented."""

    risk_category: RiskCategory
    """Fixed English risk category key."""

    severity: Severity
    """Severity level of the violation."""

    rationale: str = Field(min_length=1)
    """Explanation written in the contract language (en or vi)."""


class ViolationList(BaseModel):
    """Output schema for the Policy Compliance & Mapping Agent (Req 2.4, 2.5)."""

    violations: list[Violation]
    """Zero or more violations; a clause with no violations contributes no entries."""


# ---------------------------------------------------------------------------
# Risk Simulation schemas
# ---------------------------------------------------------------------------


class SimulationResult(BaseModel):
    """Outcome of running a single risk scenario against the contract (Req 2.6)."""

    scenario_key: ScenarioKey
    """Identifies which of the five fixed scenarios was simulated."""

    impact_score: Annotated[int, Field(ge=0, le=100)]
    """Numeric impact score in the range [0, 100]."""

    affected_clause_ids: list[str]
    """Clause identifiers that are materially affected by this scenario."""

    narrative: str = Field(min_length=1)
    """Human-readable explanation of the scenario outcome, in the contract language."""


class SimulationResultList(BaseModel):
    """Output schema for the Risk Simulation Agent (Req 2.6).

    Exactly five results are required — one per ``ScenarioKey``.
    """

    simulations: Annotated[list[SimulationResult], Field(min_length=5, max_length=5)]
    """Exactly five simulation results, one per scenario key."""


# ---------------------------------------------------------------------------
# Recommendation schemas
# ---------------------------------------------------------------------------


class Recommendation(BaseModel):
    """A suggested redline for a single contract clause (Req 2.7)."""

    clause_id: str
    """Must match a ``clause_id`` from the corresponding ``ClauseList``."""

    original_text: str
    """Verbatim original clause text — never paraphrased."""

    proposed_text: str
    """Revised clause text that addresses the identified risks."""

    change_rationale: str
    """Explanation of why the change is recommended, in the contract language."""


class RecommendationList(BaseModel):
    """Output schema for the Recommendation Agent (Req 2.7)."""

    recommendations: list[Recommendation]
    """One recommendation per clause that requires changes; may be empty."""


# ---------------------------------------------------------------------------
# Risk scoring schemas
# ---------------------------------------------------------------------------


class PerCategoryScores(BaseModel):
    """Breakdown of the overall risk score by category (Req 4.1, 4.2)."""

    legal: Annotated[int, Field(ge=0, le=100)]
    """Legal risk score in [0, 100]."""

    financial: Annotated[int, Field(ge=0, le=100)]
    """Financial risk score in [0, 100]."""

    operational: Annotated[int, Field(ge=0, le=100)]
    """Operational risk score in [0, 100]."""

    compliance: Annotated[int, Field(ge=0, le=100)]
    """Compliance risk score in [0, 100]."""

    data_privacy: Annotated[int, Field(ge=0, le=100)]
    """Data-privacy risk score in [0, 100]."""


# ---------------------------------------------------------------------------
# Governance Report (final pipeline output)
# ---------------------------------------------------------------------------


class GovernanceReport(BaseModel):
    """Complete governance audit report produced at the end of the pipeline (Req 4.1, 4.2, 4.5).

    This is the top-level object returned to the API layer and ultimately
    serialised to JSON for the frontend.  It aggregates every intermediate
    agent output together with computed risk scores and an audit trail.
    """

    job_id: str
    """Unique identifier for the audit job that produced this report."""

    language: Language
    """Dominant language of the analysed contract."""

    headline: str
    """One-line summary of the overall audit outcome."""

    executive_summary: str
    """Multi-sentence executive summary written in the contract language."""

    top_risks: list[str]
    """Ordered list of the most significant risk descriptions (highest first)."""

    risk_score: Annotated[int, Field(ge=0, le=100)]
    """Aggregate risk score across all categories, in [0, 100]."""

    per_category_scores: PerCategoryScores
    """Risk score broken down by the five risk categories."""

    clauses: list[Clause]
    """All clauses extracted from the contract."""

    clause_analyses: list[ClauseAnalysis]
    """Classification and summary for each extracted clause."""

    violations: list[Violation]
    """All policy violations detected across all clauses."""

    simulations: list[SimulationResult]
    """Results of the five fixed risk-scenario simulations."""

    recommendations: list[Recommendation]
    """Suggested redlines for clauses that require changes."""

    audit_trail: list[dict]  # AuditEntry as dict for transport
    """Ordered log of agent invocations and intermediate outputs (Req 4.5)."""
