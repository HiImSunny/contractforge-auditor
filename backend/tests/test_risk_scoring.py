"""
Property-based tests for risk_scoring.py.

Feature: contractforge-auditor

Property 7: band(score) is a total function on [0, 100]
Property 8: per-category score formula with cap
Property 9: overall risk score formula with rounded weighted mean
Property 10: scoring idempotence under (category, severity) multiset preservation

Validates: Requirements 3.2, 4.1, 4.2, 4.4
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.risk_scoring import (
    CATEGORY_WEIGHTS,
    SEVERITY_WEIGHTS,
    band,
    score,
)

CATEGORIES = list(CATEGORY_WEIGHTS.keys())
SEVERITIES = list(SEVERITY_WEIGHTS.keys())

# ── Property 7: band() is total on [0, 100] ──────────────────────────────────

@given(st.integers(min_value=0, max_value=100))
def test_band_total_function(s):
    """Property 7: band(score) returns green/amber/red for every score in [0,100]."""
    result = band(s)
    assert result in ("green", "amber", "red")

@pytest.mark.parametrize("s,expected", [
    (0, "green"), (33, "green"), (34, "amber"), (66, "amber"),
    (67, "red"), (100, "red"),
])
def test_band_boundaries(s, expected):
    assert band(s) == expected

# ── Property 8: per-category score formula with cap ──────────────────────────

@given(st.lists(
    st.fixed_dictionaries({
        "risk_category": st.sampled_from(CATEGORIES),
        "severity": st.sampled_from(SEVERITIES),
    }),
    max_size=20,
))
def test_per_category_score_formula(violations):
    """Property 8: per_category[c] == min(100, sum of weights for that category)."""
    per_cat, _ = score(violations)
    for cat in CATEGORIES:
        expected_raw = sum(
            SEVERITY_WEIGHTS[v["severity"]]
            for v in violations
            if v["risk_category"] == cat
        )
        assert per_cat[cat] == min(100, expected_raw)

# ── Property 9: overall risk score formula ───────────────────────────────────

@given(st.lists(
    st.fixed_dictionaries({
        "risk_category": st.sampled_from(CATEGORIES),
        "severity": st.sampled_from(SEVERITIES),
    }),
    max_size=20,
))
def test_overall_score_formula(violations):
    """Property 9: overall == round(weighted mean of per-category scores)."""
    per_cat, overall = score(violations)
    expected = round(sum(per_cat[c] * CATEGORY_WEIGHTS[c] for c in CATEGORY_WEIGHTS))
    assert overall == expected
    assert 0 <= overall <= 100

# ── Property 10: scoring idempotence ─────────────────────────────────────────

@given(st.lists(
    st.fixed_dictionaries({
        "risk_category": st.sampled_from(CATEGORIES),
        "severity": st.sampled_from(SEVERITIES),
    }),
    max_size=20,
))
def test_scoring_idempotence(violations):
    """Property 10: score(V) == score(V) across repeated invocations."""
    per1, ov1 = score(violations)
    per2, ov2 = score(violations)
    assert per1 == per2
    assert ov1 == ov2

# ── Worked example from design §Risk Scoring Algorithm ───────────────────────

def test_worked_example():
    """Asserts the exact worked example from design §Risk Scoring Algorithm."""
    violations = [
        {"risk_category": "legal", "severity": "high"},
        {"risk_category": "legal", "severity": "medium"},
        {"risk_category": "financial", "severity": "critical"},
        {"risk_category": "financial", "severity": "critical"},
        {"risk_category": "financial", "severity": "high"},
        {"risk_category": "data_privacy", "severity": "critical"},
        {"risk_category": "data_privacy", "severity": "high"},
        {"risk_category": "data_privacy", "severity": "high"},
        {"risk_category": "compliance", "severity": "low"},
        {"risk_category": "operational", "severity": "medium"},
    ]
    per_cat, overall = score(violations)
    assert per_cat["legal"] == 45
    assert per_cat["financial"] == 100
    assert per_cat["operational"] == 15
    assert per_cat["compliance"] == 5
    assert per_cat["data_privacy"] == 100
    assert overall == 50
