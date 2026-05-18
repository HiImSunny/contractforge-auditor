"""
Policy Compliance & Mapping Agent for ContractForge Auditor.

Compares each extracted contract clause against the supplied policy rules
and identifies violations.  Calls the Gemini API via ``gemini_client.invoke``
and returns a partial-state dict containing ``violations``.

References
----------
- Req 2.4  — Policy rule violation detection with severity classification.
- Req 9.4  — Policy Mapping Agent prompt and output schema.
"""

from __future__ import annotations

import csv
import io
import json

from app.agents import gemini_client
from app.agents.prompts import POLICY_MAPPING_PROMPT
from app.agents.schemas import ViolationList
from app.agents.state import PipelineState


def run(state: PipelineState) -> dict:
    """Execute the Policy Compliance & Mapping Agent.

    Reads ``clauses``, ``language``, ``job_id``, and ``policy_text`` from
    *state*, parses the policy CSV into structured rule dicts, formats the
    ``POLICY_MAPPING_PROMPT``, calls Gemini, and returns a partial-state dict
    containing ``violations``.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  Must contain:
        - ``clauses``     — list of clause dicts from the ingestion agent.
        - ``language``    — ``"en"`` or ``"vi"``.
        - ``job_id``      — UUID v4 identifying the current analysis job.
        - ``policy_text`` — raw CSV (or plain text) policy document; may be
                            absent or empty, in which case no violations are
                            expected.

    Returns
    -------
    dict
        ``{"violations": [<Violation as dict>, ...]}``

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so the pipeline can handle it at the orchestration layer.
    """
    clauses: list[dict] = state["clauses"]
    language: str = state["language"]
    job_id: str = state["job_id"]
    policy_text: str = state.get("policy_text", "") or ""

    # Parse policy_text as CSV rows into a list of policy rule dicts.
    # Each expected CSV row: policy_rule_id, risk_category, severity,
    #                        description_en, description_vi
    policy_rules = _parse_policy(policy_text, language)

    prompt = POLICY_MAPPING_PROMPT.format(
        language=language,
        clauses_json=json.dumps(clauses, ensure_ascii=False),
        policy_rules_json=json.dumps(policy_rules, ensure_ascii=False),
    )

    result: ViolationList = gemini_client.invoke(
        prompt,
        ViolationList,
        "policy_mapping",
        job_id,
    )

    return {"violations": [v.model_dump() for v in result.violations]}


def _parse_policy(policy_text: str, language: str) -> list[dict]:
    """Parse CSV or plain-text policy into a list of rule dicts.

    Attempts to parse *policy_text* as a CSV with a header row containing at
    least ``policy_rule_id``, ``risk_category``, ``severity``, and either
    ``description_en`` or ``description_vi``.  Falls back to a single
    plain-text rule dict when CSV parsing fails or the text is empty.

    Parameters
    ----------
    policy_text:
        Raw policy document content (CSV or plain text).
    language:
        Contract language (``"en"`` or ``"vi"``).  Used to select the
        appropriate description column when both are present.

    Returns
    -------
    list[dict]
        A list of rule dicts, each with keys ``policy_rule_id``,
        ``risk_category``, ``severity``, and ``description``.
    """
    if not policy_text.strip():
        return []

    rules: list[dict] = []
    try:
        reader = csv.DictReader(io.StringIO(policy_text))
        for row in reader:
            # Prefer the language-specific description column; fall back to EN.
            desc_key = "description_vi" if language == "vi" else "description_en"
            desc = row.get(desc_key) or row.get("description_en", "")
            rules.append(
                {
                    "policy_rule_id": row.get("policy_rule_id", ""),
                    "risk_category": row.get("risk_category", ""),
                    "severity": row.get("severity", ""),
                    "description": desc,
                }
            )
    except Exception:
        # Fallback: treat the entire text as a single plain-text rule.
        rules = [{"policy_rule_id": "POL-001", "description": policy_text}]

    return rules
