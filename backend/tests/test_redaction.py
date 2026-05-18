"""
Property-based tests for redaction.py.

Feature: contractforge-auditor

Property 13: For every Hypothesis-generated string, redact(s) produces a
string with zero matches for the email regex, phone regex, and
government-id regex set.

Validates: Requirements 5.4
"""
import re
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.redaction import PII_PATTERNS, redact

# Extract the compiled patterns for post-redaction verification
EMAIL_PATTERN = PII_PATTERNS[0][0]
PHONE_PATTERN = PII_PATTERNS[1][0]
GOVID_PATTERNS = [p for p, _ in PII_PATTERNS[2:]]

@given(st.text(max_size=500))
def test_redact_removes_email(s):
    """Property 13a: redact(s) has zero email matches."""
    result = redact(s)
    assert EMAIL_PATTERN.search(result) is None

@given(st.text(max_size=500))
def test_redact_removes_phone(s):
    """Property 13b: redact(s) has zero phone matches."""
    result = redact(s)
    assert PHONE_PATTERN.search(result) is None

@given(st.text(max_size=500))
def test_redact_removes_govid(s):
    """Property 13c: redact(s) has zero government-id matches."""
    result = redact(s)
    for pattern in GOVID_PATTERNS:
        assert pattern.search(result) is None

# Concrete examples
def test_redact_email_example():
    assert "user@example.com" not in redact("Contact user@example.com for details")

def test_redact_phone_example():
    assert "+1 555 123 4567" not in redact("Call +1 555 123 4567 now")

def test_redact_ssn_example():
    assert "123-45-6789" not in redact("SSN: 123-45-6789")

def test_redact_preserves_non_pii():
    text = "The contract value is $50,000 for 12 months."
    assert redact(text) == text
