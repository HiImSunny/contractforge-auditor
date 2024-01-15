"""
Worked example test for risk_scoring.py.

Feature: contractforge-auditor

This test validates the exact worked example from design §Risk Scoring Algorithm.
The test asserts that score(...) returns the expected per-category scores and
overall score for the ten-violation worked example.

Validates: Requirements 4.1, 4.2, 4.3, 4.5
"""
import pytest

from app.services.risk_scoring import score


def test_risk_scoring_worked_example():
    """
    Asserts the exact worked example from design §Risk Scoring Algorithm.

    Violations:
      1. legal, high (30)
      2. legal, medium (15)
      3. financial, critical (50)
      4. financial, critical (50)
      5. financial, high (30)
      6. data_privacy, critical (50)
      7. data_privacy, high (30)
      8. data_privacy, high (30)
      9. compliance, low (5)
      10. operational, medium (15)

    Expected per-category sums (before cap):
      - legal: 30 + 15 = 45
      - financial: 50 + 50 + 30 = 130 → capped to 100
      - operational: 15
      - compliance: 5
      - data_privacy: 50 + 30 + 30 = 110 → capped to 100

    Expected weighted overall:
      0.25*45 + 0.20*100 + 0.15*15 + 0.25*5 + 0.15*100
      = 11.25 + 20.00 + 2.25 + 1.25 + 15.00
      = 49.75
      round(49.75) = 50
    """
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

    per_category, overall = score(violations)

    # Assert per-category scores
    assert per_category["legal"] == 45
    assert per_category["financial"] == 100
    assert per_category["operational"] == 15
    assert per_category["compliance"] == 5
    assert per_category["data_privacy"] == 100

    # Assert overall score
    assert overall == 50
