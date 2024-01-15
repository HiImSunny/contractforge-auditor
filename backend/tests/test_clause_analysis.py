"""
Property-based tests for the Clause Analysis Agent.

Feature: contractforge-auditor

Property 3: Clause analysis is a 1-to-1 function over clause_id
  For any list of Clauses passed to the Clause Analysis Agent, the emitted
  `analyses` list has exactly the same length and the multiset of `clause_id`
  values is preserved.

Validates: Requirements 2.3
"""
import json
import uuid
from collections import Counter
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agents.clause_analysis import run
from app.agents.schemas import Clause, ClauseAnalysis, ClauseAnalysisList
from app.services import job_store


# ── Hypothesis strategies ────────────────────────────────────────────────────

@st.composite
def clause_strategy(draw):
    """Generate a valid Clause with random but consistent data."""
    clause_id = draw(st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
        min_size=1,
        max_size=32,
    ))
    heading = draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    text = draw(st.text(min_size=1, max_size=500))
    language = draw(st.sampled_from(["en", "vi"]))
    char_start = draw(st.integers(min_value=0, max_value=100))
    char_end = draw(st.integers(min_value=char_start + 1, max_value=char_start + 500))

    return {
        "clause_id": clause_id,
        "heading": heading,
        "text": text,
        "language": language,
        "char_span": {
            "start": char_start,
            "end": char_end,
        },
    }


@st.composite
def clause_analysis_strategy(draw, clause_ids):
    """Generate a ClauseAnalysis for a given clause_id."""
    clause_id = draw(st.sampled_from(clause_ids))
    clause_type = draw(st.sampled_from([
        "term", "termination", "payment", "confidentiality", "data_protection",
        "liability", "indemnification", "force_majeure", "governing_law",
        "ip_assignment", "warranty", "service_level", "compliance", "other",
    ]))
    summary = draw(st.text(min_size=1, max_size=300))
    key_terms = draw(st.lists(
        st.text(min_size=1, max_size=50),
        max_size=10,
    ))

    return {
        "clause_id": clause_id,
        "clause_type": clause_type,
        "summary": summary,
        "key_terms": key_terms,
    }


# ── Property 3: Clause analysis preserves clause_id multiset ────────────────

@given(
    clauses=st.lists(clause_strategy(), min_size=1, max_size=20),
    language=st.sampled_from(["en", "vi"]),
)
@settings(max_examples=50)
def test_clause_analysis_preserves_clause_ids(clauses, language):
    """Property 3: Emitted analyses have same length and clause_id multiset as input.

    For any list of Clauses passed to the Clause Analysis Agent, the emitted
    `analyses` list has exactly the same length and the multiset of `clause_id`
    values is preserved.

    **Validates: Requirements 2.3**
    """
    # Ensure all clauses have the same language for consistency
    for clause in clauses:
        clause["language"] = language

    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    # Extract the clause_ids from input
    input_clause_ids = [c["clause_id"] for c in clauses]
    input_multiset = Counter(input_clause_ids)

    # Mock the Gemini call to return a valid ClauseAnalysisList
    # with one analysis per input clause, preserving clause_ids
    def mock_gemini_call(prompt):
        analyses = []
        for clause in clauses:
            analyses.append({
                "clause_id": clause["clause_id"],
                "clause_type": "term",
                "summary": f"Summary of {clause['clause_id']}",
                "key_terms": ["key1", "key2"],
            })
        response = {
            "analyses": analyses,
        }
        return json.dumps(response)

    # Create the pipeline state
    state = {
        "job_id": job_id,
        "clauses": clauses,
        "language": language,
    }

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_gemini_call):
        result = run(state)

    # Extract the clause_ids from output
    output_clause_analyses = result["clause_analyses"]
    output_clause_ids = [a["clause_id"] for a in output_clause_analyses]
    output_multiset = Counter(output_clause_ids)

    # Assert: same length
    assert len(output_clause_analyses) == len(clauses), (
        f"Expected {len(clauses)} analyses, got {len(output_clause_analyses)}"
    )

    # Assert: same multiset of clause_ids
    assert output_multiset == input_multiset, (
        f"Clause ID multiset mismatch. Input: {input_multiset}, Output: {output_multiset}"
    )


# ── Edge case: empty clause list ─────────────────────────────────────────────

def test_clause_analysis_empty_list():
    """Edge case: empty clause list should produce empty analyses list."""
    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    clauses = []
    language = "en"

    def mock_gemini_call(prompt):
        response = {"analyses": []}
        return json.dumps(response)

    state = {
        "job_id": job_id,
        "clauses": clauses,
        "language": language,
    }

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_gemini_call):
        result = run(state)

    assert result["clause_analyses"] == []


# ── Edge case: single clause ─────────────────────────────────────────────────

def test_clause_analysis_single_clause():
    """Edge case: single clause should produce single analysis with matching clause_id."""
    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    clauses = [{
        "clause_id": "C-001",
        "heading": "Term",
        "text": "This agreement commences on the effective date.",
        "language": "en",
        "char_span": {"start": 0, "end": 50},
    }]
    language = "en"

    def mock_gemini_call(prompt):
        response = {
            "analyses": [{
                "clause_id": "C-001",
                "clause_type": "term",
                "summary": "Agreement commencement clause.",
                "key_terms": ["effective date", "commencement"],
            }],
        }
        return json.dumps(response)

    state = {
        "job_id": job_id,
        "clauses": clauses,
        "language": language,
    }

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_gemini_call):
        result = run(state)

    assert len(result["clause_analyses"]) == 1
    assert result["clause_analyses"][0]["clause_id"] == "C-001"


# ── Edge case: duplicate clause_ids in input ─────────────────────────────────

def test_clause_analysis_duplicate_clause_ids():
    """Edge case: duplicate clause_ids in input should be preserved in output."""
    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    clauses = [
        {
            "clause_id": "C-001",
            "heading": "Term",
            "text": "First occurrence.",
            "language": "en",
            "char_span": {"start": 0, "end": 20},
        },
        {
            "clause_id": "C-001",  # Duplicate
            "heading": "Term",
            "text": "Second occurrence.",
            "language": "en",
            "char_span": {"start": 20, "end": 40},
        },
        {
            "clause_id": "C-002",
            "heading": "Payment",
            "text": "Payment terms.",
            "language": "en",
            "char_span": {"start": 40, "end": 60},
        },
    ]
    language = "en"

    def mock_gemini_call(prompt):
        analyses = []
        for clause in clauses:
            analyses.append({
                "clause_id": clause["clause_id"],
                "clause_type": "term",
                "summary": f"Summary of {clause['clause_id']}",
                "key_terms": [],
            })
        response = {"analyses": analyses}
        return json.dumps(response)

    state = {
        "job_id": job_id,
        "clauses": clauses,
        "language": language,
    }

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_gemini_call):
        result = run(state)

    # Check length preservation
    assert len(result["clause_analyses"]) == 3

    # Check multiset preservation (two C-001, one C-002)
    output_ids = [a["clause_id"] for a in result["clause_analyses"]]
    assert Counter(output_ids) == Counter(["C-001", "C-001", "C-002"])


# ── Edge case: Vietnamese language ───────────────────────────────────────────

def test_clause_analysis_vietnamese():
    """Edge case: Vietnamese clauses should preserve clause_ids correctly."""
    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    clauses = [
        {
            "clause_id": "C-001",
            "heading": "Điều khoản",
            "text": "Hợp đồng này bắt đầu từ ngày hiệu lực.",
            "language": "vi",
            "char_span": {"start": 0, "end": 50},
        },
        {
            "clause_id": "C-002",
            "heading": "Thanh toán",
            "text": "Bên A thanh toán phí dịch vụ hàng tháng.",
            "language": "vi",
            "char_span": {"start": 50, "end": 100},
        },
    ]
    language = "vi"

    def mock_gemini_call(prompt):
        analyses = []
        for clause in clauses:
            analyses.append({
                "clause_id": clause["clause_id"],
                "clause_type": "payment" if "thanh toán" in clause["text"].lower() else "term",
                "summary": f"Tóm tắt của {clause['clause_id']}",
                "key_terms": ["từ khóa"],
            })
        response = {"analyses": analyses}
        return json.dumps(response)

    state = {
        "job_id": job_id,
        "clauses": clauses,
        "language": language,
    }

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_gemini_call):
        result = run(state)

    assert len(result["clause_analyses"]) == 2
    output_ids = [a["clause_id"] for a in result["clause_analyses"]]
    assert Counter(output_ids) == Counter(["C-001", "C-002"])
