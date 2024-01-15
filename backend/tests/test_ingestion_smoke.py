"""
Smoke tests for ingestion.py.

Feature: contractforge-auditor

Task 2.7: Add backend/tests/test_ingestion_smoke.py exercising ingestion.run
against a tiny EN string and a tiny VI string with the Gemini client mocked
to return canned JSON.

Validates: Requirements 1.6, 1.7, 1.8, 1.9, 2.3, 6.1, 6.2, 6.4, 9.1, 9.2, 9.3
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.agents.ingestion import run
from app.agents.schemas import ClauseList


# ── Canned responses for mocking ─────────────────────────────────────────────

CANNED_EN_RESPONSE = {
    "language": "en",
    "clauses": [
        {
            "clause_id": "C-001",
            "heading": "1. Term",
            "text": "This Agreement commences on the Effective Date.",
            "language": "en",
            "char_span": {"start": 0, "end": 47},
        },
        {
            "clause_id": "C-002",
            "heading": "2. Payment",
            "text": "Payment shall be made within 30 days of invoice.",
            "language": "en",
            "char_span": {"start": 48, "end": 96},
        },
    ],
}

CANNED_VI_RESPONSE = {
    "language": "vi",
    "clauses": [
        {
            "clause_id": "C-001",
            "heading": "1. Thời hạn",
            "text": "Hợp đồng này có hiệu lực từ ngày ký kết.",
            "language": "vi",
            "char_span": {"start": 0, "end": 40},
        },
        {
            "clause_id": "C-002",
            "heading": "2. Thanh toán",
            "text": "Thanh toán phải được thực hiện trong vòng 30 ngày.",
            "language": "vi",
            "char_span": {"start": 41, "end": 92},
        },
    ],
}


# ── Tests ────────────────────────────────────────────────────────────────────


def test_ingestion_smoke_en():
    """Smoke test: ingestion.run with tiny EN contract and mocked Gemini."""
    tiny_en_contract = "This Agreement commences on the Effective Date. Payment shall be made within 30 days of invoice."

    with patch("app.agents.gemini_client._call_gemini") as mock_gemini:
        # Mock Gemini to return the canned EN response as JSON
        mock_gemini.return_value = json.dumps(CANNED_EN_RESPONSE)

        # Mock the audit log to avoid side effects
        with patch("app.agents.gemini_client._write_audit"):
            state = {
                "job_id": "test-job-001",
                "contract_text": tiny_en_contract,
            }

            result = run(state)

            # Assertions
            assert "clauses" in result
            assert "language" in result
            assert result["language"] == "en"
            assert len(result["clauses"]) == 2

            # Check first clause
            c1 = result["clauses"][0]
            assert c1["clause_id"] == "C-001"
            assert c1["heading"] == "1. Term"
            assert c1["text"] == "This Agreement commences on the Effective Date."
            assert c1["language"] == "en"
            assert c1["char_span"]["start"] == 0
            assert c1["char_span"]["end"] == 47

            # Check second clause
            c2 = result["clauses"][1]
            assert c2["clause_id"] == "C-002"
            assert c2["heading"] == "2. Payment"
            assert c2["text"] == "Payment shall be made within 30 days of invoice."
            assert c2["language"] == "en"
            assert c2["char_span"]["start"] == 48
            assert c2["char_span"]["end"] == 96


def test_ingestion_smoke_vi():
    """Smoke test: ingestion.run with tiny VI contract and mocked Gemini."""
    tiny_vi_contract = "Hợp đồng này có hiệu lực từ ngày ký kết. Thanh toán phải được thực hiện trong vòng 30 ngày."

    with patch("app.agents.gemini_client._call_gemini") as mock_gemini:
        # Mock Gemini to return the canned VI response as JSON
        mock_gemini.return_value = json.dumps(CANNED_VI_RESPONSE)

        # Mock the audit log to avoid side effects
        with patch("app.agents.gemini_client._write_audit"):
            state = {
                "job_id": "test-job-002",
                "contract_text": tiny_vi_contract,
            }

            result = run(state)

            # Assertions
            assert "clauses" in result
            assert "language" in result
            assert result["language"] == "vi"
            assert len(result["clauses"]) == 2

            # Check first clause
            c1 = result["clauses"][0]
            assert c1["clause_id"] == "C-001"
            assert c1["heading"] == "1. Thời hạn"
            assert c1["text"] == "Hợp đồng này có hiệu lực từ ngày ký kết."
            assert c1["language"] == "vi"
            assert c1["char_span"]["start"] == 0
            assert c1["char_span"]["end"] == 40

            # Check second clause
            c2 = result["clauses"][1]
            assert c2["clause_id"] == "C-002"
            assert c2["heading"] == "2. Thanh toán"
            assert c2["text"] == "Thanh toán phải được thực hiện trong vòng 30 ngày."
            assert c2["language"] == "vi"
            assert c2["char_span"]["start"] == 41
            assert c2["char_span"]["end"] == 92


def test_ingestion_smoke_empty_contract():
    """Smoke test: ingestion.run with empty contract returns empty clauses."""
    with patch("app.agents.gemini_client._call_gemini") as mock_gemini:
        # Mock Gemini to return empty clauses for empty input
        mock_gemini.return_value = json.dumps({
            "language": "en",
            "clauses": [],
        })

        # Mock the audit log to avoid side effects
        with patch("app.agents.gemini_client._write_audit"):
            state = {
                "job_id": "test-job-003",
                "contract_text": "",
            }

            result = run(state)

            # Assertions
            assert result["language"] == "en"
            assert result["clauses"] == []


def test_ingestion_smoke_validates_schema():
    """Smoke test: ingestion.run validates response against ClauseList schema."""
    with patch("app.agents.gemini_client._call_gemini") as mock_gemini:
        # Mock Gemini to return valid JSON that matches the schema
        mock_gemini.return_value = json.dumps(CANNED_EN_RESPONSE)

        # Mock the audit log to avoid side effects
        with patch("app.agents.gemini_client._write_audit"):
            state = {
                "job_id": "test-job-004",
                "contract_text": "Test contract",
            }

            result = run(state)

            # The result should be a dict with the expected structure
            assert isinstance(result, dict)
            assert "language" in result
            assert "clauses" in result
            assert isinstance(result["clauses"], list)
            assert all(isinstance(c, dict) for c in result["clauses"])
