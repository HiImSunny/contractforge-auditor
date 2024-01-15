"""
Property-based tests for taxonomy stability and output validation.

Feature: contractforge-auditor

Property 4: Policy mapping output references only known ids and taxonomy keys
            — every Violation has clause_id ∈ input clause ids,
            policy_rule_id ∈ input policy rule ids, risk_category ∈
            {legal, financial, operational, compliance, data_privacy},
            and severity ∈ {low, medium, high, critical}.

Property 5: Risk Simulation always covers exactly the five MVP scenarios
            — the set of scenario_key values equals {force_majeure,
            penalty_delay, data_breach, termination, payment_default},
            and every impact_score is in [0, 100].

Property 6: Recommendations are gated on severity
            — the number of emitted Recommendations equals the number of
            Violations whose severity is in {medium, high, critical}.

Property 16: Taxonomy stability across languages
             — for any contract whose detected language is en or vi,
             every risk_category, severity, and scenario_key value
             emitted by the pipeline is drawn from its fixed English-keyed
             enumeration.

Validates: Requirements 2.4, 2.5, 2.6, 4.5, 6.1, 9.5
"""

import json
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agents.schemas import (
    Violation,
    ViolationList,
    SimulationResult,
    SimulationResultList,
    Recommendation,
    RecommendationList,
)
from app.agents import policy_mapping, risk_simulation, recommendation
from app.services import job_store

# ── Shared constants ─────────────────────────────────────────────────────────

VALID_RISK_CATEGORIES = {"legal", "financial", "operational", "compliance", "data_privacy"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_SCENARIO_KEYS = {"force_majeure", "penalty_delay", "data_breach", "termination", "payment_default"}


# ── Property 4: Policy mapping output references only known ids and taxonomy keys ──

@given(
    num_clauses=st.integers(min_value=1, max_value=5),
    num_policy_rules=st.integers(min_value=0, max_value=5),
    num_violations=st.integers(min_value=0, max_value=5),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=20)
def test_policy_mapping_references_known_ids(num_clauses, num_policy_rules, num_violations, language):
    """Property 4: Every Violation references only known clause_id, policy_rule_id, and valid taxonomy keys.

    **Validates: Requirements 2.4, 6.1**
    """
    # Generate test clauses
    clauses = [
        {
            "clause_id": f"C-{i:03d}",
            "heading": f"Section {i}",
            "text": f"Clause text {i}",
            "language": language,
            "char_span": {"start": i * 100, "end": (i + 1) * 100},
        }
        for i in range(num_clauses)
    ]
    clause_ids = {c["clause_id"] for c in clauses}

    # Generate test policy rules
    policy_rules = [
        {
            "policy_rule_id": f"POL-{i:03d}",
            "risk_category": list(VALID_RISK_CATEGORIES)[i % len(VALID_RISK_CATEGORIES)],
            "severity": list(VALID_SEVERITIES)[i % len(VALID_SEVERITIES)],
            "description": f"Policy rule {i}",
        }
        for i in range(num_policy_rules)
    ]
    policy_rule_ids = {p["policy_rule_id"] for p in policy_rules}

    # Generate test violations that reference known ids
    violations = [
        {
            "clause_id": list(clause_ids)[i % len(clause_ids)],
            "policy_rule_id": list(policy_rule_ids)[i % len(policy_rule_ids)] if policy_rule_ids else "POL-001",
            "risk_category": list(VALID_RISK_CATEGORIES)[i % len(VALID_RISK_CATEGORIES)],
            "severity": list(VALID_SEVERITIES)[i % len(VALID_SEVERITIES)],
            "rationale": f"Violation rationale {i}",
        }
        for i in range(num_violations)
    ]

    # Mock Gemini to return our test violations
    mock_response = ViolationList(violations=[Violation(**v) for v in violations])

    job_id = "test-job-001"
    job_store.put(job_id)

    state = {
        "clauses": clauses,
        "language": language,
        "job_id": job_id,
        "policy_text": "",
    }

    with patch("app.agents.gemini_client.invoke", return_value=mock_response):
        result = policy_mapping.run(state)

    # Verify all returned violations reference known ids and valid taxonomy keys
    for violation in result["violations"]:
        assert violation["clause_id"] in clause_ids, (
            f"Violation references unknown clause_id: {violation['clause_id']}"
        )
        if policy_rule_ids:
            assert violation["policy_rule_id"] in policy_rule_ids, (
                f"Violation references unknown policy_rule_id: {violation['policy_rule_id']}"
            )
        assert violation["risk_category"] in VALID_RISK_CATEGORIES, (
            f"Violation has invalid risk_category: {violation['risk_category']}"
        )
        assert violation["severity"] in VALID_SEVERITIES, (
            f"Violation has invalid severity: {violation['severity']}"
        )


# ── Property 5: Risk Simulation covers exactly five MVP scenarios ──────────────

@given(
    num_clauses=st.integers(min_value=1, max_value=5),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=20)
def test_risk_simulation_covers_five_scenarios(num_clauses, language):
    """Property 5: Risk Simulation emits exactly the five MVP scenario keys with impact_score ∈ [0, 100].

    **Validates: Requirements 2.5**
    """
    # Generate test clauses
    clauses = [
        {
            "clause_id": f"C-{i:03d}",
            "heading": f"Section {i}",
            "text": f"Clause text {i}",
            "language": language,
            "char_span": {"start": i * 100, "end": (i + 1) * 100},
        }
        for i in range(num_clauses)
    ]
    clause_ids = [c["clause_id"] for c in clauses]

    # Generate exactly five simulation results, one per scenario key
    simulations = [
        {
            "scenario_key": key,
            "impact_score": (i * 20) % 101,  # Vary impact scores
            "affected_clause_ids": clause_ids[:max(1, len(clause_ids) // 2)],
            "narrative": f"Narrative for {key}",
        }
        for i, key in enumerate(VALID_SCENARIO_KEYS)
    ]

    mock_response = SimulationResultList(simulations=[
        SimulationResult(**s) for s in simulations
    ])

    job_id = "test-job-002"
    job_store.put(job_id)

    state = {
        "clauses": clauses,
        "language": language,
        "job_id": job_id,
    }

    with patch("app.agents.gemini_client.invoke", return_value=mock_response):
        result = risk_simulation.run(state)

    # Verify exactly five scenarios are returned
    assert len(result["simulations"]) == 5, (
        f"Expected exactly 5 simulations, got {len(result['simulations'])}"
    )

    # Verify all five scenario keys are present
    returned_keys = {s["scenario_key"] for s in result["simulations"]}
    assert returned_keys == VALID_SCENARIO_KEYS, (
        f"Expected scenario keys {VALID_SCENARIO_KEYS}, got {returned_keys}"
    )

    # Verify all impact_scores are in [0, 100]
    for sim in result["simulations"]:
        assert 0 <= sim["impact_score"] <= 100, (
            f"Simulation {sim['scenario_key']} has invalid impact_score: {sim['impact_score']}"
        )


# ── Property 6: Recommendations are gated on severity ──────────────────────────

@given(
    num_clauses=st.integers(min_value=1, max_value=5),
    num_violations=st.integers(min_value=0, max_value=5),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=20)
def test_recommendations_gated_on_severity(num_clauses, num_violations, language):
    """Property 6: Number of Recommendations equals number of Violations with severity ∈ {medium, high, critical}.

    **Validates: Requirements 2.6**
    """
    # Generate test clauses
    clauses = [
        {
            "clause_id": f"C-{i:03d}",
            "heading": f"Section {i}",
            "text": f"Clause text {i}",
            "language": language,
            "char_span": {"start": i * 100, "end": (i + 1) * 100},
        }
        for i in range(num_clauses)
    ]
    clause_id_map = {c["clause_id"]: c for c in clauses}

    # Generate test violations
    violations = [
        {
            "clause_id": list(clause_id_map.keys())[i % len(clause_id_map)],
            "policy_rule_id": f"POL-{i:03d}",
            "risk_category": list(VALID_RISK_CATEGORIES)[i % len(VALID_RISK_CATEGORIES)],
            "severity": list(VALID_SEVERITIES)[i % len(VALID_SEVERITIES)],
            "rationale": f"Violation rationale {i}",
        }
        for i in range(num_violations)
    ]

    # Count violations with severity in {medium, high, critical}
    expected_recommendation_count = sum(
        1 for v in violations
        if v["severity"] in {"medium", "high", "critical"}
    )

    # Generate recommendations matching the expected count
    recommendations = [
        {
            "clause_id": v["clause_id"],
            "original_text": clause_id_map[v["clause_id"]]["text"],
            "proposed_text": clause_id_map[v["clause_id"]]["text"] + " [AMENDED]",
            "change_rationale": f"Addresses {v['policy_rule_id']}",
        }
        for v in violations
        if v["severity"] in {"medium", "high", "critical"}
    ]

    mock_response = RecommendationList(recommendations=[
        Recommendation(**r) for r in recommendations
    ])

    job_id = "test-job-003"
    job_store.put(job_id)

    state = {
        "clauses": clauses,
        "violations": violations,
        "language": language,
        "job_id": job_id,
    }

    with patch("app.agents.gemini_client.invoke", return_value=mock_response):
        result = recommendation.run(state)

    # Verify the number of recommendations matches the expected count
    assert len(result["recommendations"]) == expected_recommendation_count, (
        f"Expected {expected_recommendation_count} recommendations, got {len(result['recommendations'])}"
    )


# ── Property 16: Taxonomy stability across languages ──────────────────────────

@given(
    num_clauses=st.integers(min_value=1, max_value=5),
    num_violations=st.integers(min_value=0, max_value=5),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=20)
def test_taxonomy_stability_across_languages_violations(num_clauses, num_violations, language):
    """Property 16 (Violations): risk_category and severity are always English-keyed regardless of language.

    **Validates: Requirements 4.5, 9.5**
    """
    # Generate test clauses
    clauses = [
        {
            "clause_id": f"C-{i:03d}",
            "heading": f"Section {i}",
            "text": f"Clause text {i}",
            "language": language,
            "char_span": {"start": i * 100, "end": (i + 1) * 100},
        }
        for i in range(num_clauses)
    ]
    clause_ids = [c["clause_id"] for c in clauses]

    # Generate violations with valid taxonomy keys
    violations = [
        {
            "clause_id": clause_ids[i % len(clause_ids)],
            "policy_rule_id": f"POL-{i:03d}",
            "risk_category": list(VALID_RISK_CATEGORIES)[i % len(VALID_RISK_CATEGORIES)],
            "severity": list(VALID_SEVERITIES)[i % len(VALID_SEVERITIES)],
            "rationale": f"Violation rationale {i}",
        }
        for i in range(num_violations)
    ]

    mock_response = ViolationList(violations=[Violation(**v) for v in violations])

    job_id = "test-job-004"
    job_store.put(job_id)

    state = {
        "clauses": clauses,
        "language": language,
        "job_id": job_id,
        "policy_text": "",
    }

    with patch("app.agents.gemini_client.invoke", return_value=mock_response):
        result = policy_mapping.run(state)

    # Verify all taxonomy keys are English-keyed regardless of language
    for violation in result["violations"]:
        assert violation["risk_category"] in VALID_RISK_CATEGORIES, (
            f"Violation has non-English risk_category: {violation['risk_category']}"
        )
        assert violation["severity"] in VALID_SEVERITIES, (
            f"Violation has non-English severity: {violation['severity']}"
        )


@given(
    num_clauses=st.integers(min_value=1, max_value=5),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=20)
def test_taxonomy_stability_across_languages_simulations(num_clauses, language):
    """Property 16 (Simulations): scenario_key values are always English-keyed regardless of language.

    **Validates: Requirements 4.5, 9.5**
    """
    # Generate test clauses
    clauses = [
        {
            "clause_id": f"C-{i:03d}",
            "heading": f"Section {i}",
            "text": f"Clause text {i}",
            "language": language,
            "char_span": {"start": i * 100, "end": (i + 1) * 100},
        }
        for i in range(num_clauses)
    ]
    clause_ids = [c["clause_id"] for c in clauses]

    # Generate exactly five simulation results with valid scenario keys
    simulations = [
        {
            "scenario_key": key,
            "impact_score": (i * 20) % 101,
            "affected_clause_ids": clause_ids[:max(1, len(clause_ids) // 2)],
            "narrative": f"Narrative for {key}",
        }
        for i, key in enumerate(VALID_SCENARIO_KEYS)
    ]

    mock_response = SimulationResultList(simulations=[
        SimulationResult(**s) for s in simulations
    ])

    job_id = "test-job-005"
    job_store.put(job_id)

    state = {
        "clauses": clauses,
        "language": language,
        "job_id": job_id,
    }

    with patch("app.agents.gemini_client.invoke", return_value=mock_response):
        result = risk_simulation.run(state)

    # Verify all scenario keys are English-keyed regardless of language
    for sim in result["simulations"]:
        assert sim["scenario_key"] in VALID_SCENARIO_KEYS, (
            f"Simulation has non-English scenario_key: {sim['scenario_key']}"
        )
