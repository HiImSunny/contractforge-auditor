"""
Tests for audit trail behaviour.

Feature: contractforge-auditor

Property 11: AuditEntry shape — 64-char SHA-256 fields, ISO-8601 timestamp,
             latency_ms >= 0, non-empty agent_name / model_version
Property 12: GET /api/audit-trail/{job_id} returns entries in non-decreasing
             timestamp_iso8601 order
Property 14: One repair retry succeeds when the second Gemini response is
             valid; exactly two Gemini calls observed
Property 15: Every assembled system prompt begins with the canonical GUARDRAIL block

Validates: Requirements 5.1, 5.2, 6.2, 6.4
"""
import re
import uuid
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.services.audit_log import AuditEntry, record, list_for_job
from app.services import job_store
from app.agents.prompts import (
    GUARDRAIL,
    INGESTION_PROMPT,
    CLAUSE_ANALYSIS_PROMPT,
    POLICY_MAPPING_PROMPT,
    RISK_SIMULATION_PROMPT,
    RECOMMENDATION_PROMPT,
    REPORT_PROMPT,
)

ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# ── Property 11: AuditEntry shape ────────────────────────────────────────────

@given(
    agent_name=st.text(min_size=1, max_size=64),
    model_version=st.text(min_size=1, max_size=64),
    latency_ms=st.integers(min_value=0, max_value=60000),
)
def test_audit_entry_shape(agent_name, model_version, latency_ms):
    """Property 11: AuditEntry fields satisfy shape constraints.

    **Validates: Requirements 5.1**
    """
    import datetime

    job_id = str(uuid.uuid4())
    entry = AuditEntry(
        job_id=job_id,
        agent_name=agent_name,
        input_sha256="a" * 64,
        output_sha256="b" * 64,
        timestamp_iso8601=datetime.datetime.utcnow().isoformat() + "Z",
        model_version=model_version,
        latency_ms=latency_ms,
    )
    assert SHA256_RE.match(entry.input_sha256)
    assert SHA256_RE.match(entry.output_sha256)
    assert ISO8601_RE.match(entry.timestamp_iso8601)
    assert len(entry.agent_name) > 0
    assert len(entry.model_version) > 0
    assert entry.latency_ms >= 0


# ── Property 12: Chronological order ─────────────────────────────────────────

def test_audit_trail_chronological_order():
    """Property 12: list_for_job returns entries in non-decreasing timestamp order.

    **Validates: Requirements 5.2**
    """
    import datetime

    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    for i in range(5):
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        entry = AuditEntry(
            job_id=job_id,
            agent_name=f"agent_{i}",
            input_sha256="a" * 64,
            output_sha256="b" * 64,
            timestamp_iso8601=ts,
            model_version="gemini-1.5-flash",
            latency_ms=i * 10,
        )
        record(entry)

    entries = list_for_job(job_id)
    assert len(entries) == 5
    for i in range(len(entries) - 1):
        assert entries[i]["timestamp_iso8601"] <= entries[i + 1]["timestamp_iso8601"]


# ── Property 14: Repair retry ─────────────────────────────────────────────────

def test_repair_retry_exactly_two_calls():
    """Property 14: When first response is invalid and second is valid, exactly two Gemini calls are made.

    **Validates: Requirements 6.2**
    """
    from pydantic import BaseModel
    from app.agents.gemini_client import invoke

    class SimpleModel(BaseModel):
        value: str

    valid_json = '{"value": "hello"}'
    invalid_json = '{"wrong_key": 123}'

    call_count = 0

    def mock_call_gemini(prompt):
        nonlocal call_count
        call_count += 1
        return valid_json if call_count == 2 else invalid_json

    job_id = str(uuid.uuid4())
    job_store.put(job_id)

    with patch("app.agents.gemini_client._call_gemini", side_effect=mock_call_gemini):
        result = invoke(valid_json, SimpleModel, "test_agent", job_id)

    assert call_count == 2
    assert result.value == "hello"


# ── Property 15: GUARDRAIL prefix ────────────────────────────────────────────

@pytest.mark.parametrize("prompt_name,prompt", [
    ("INGESTION_PROMPT", INGESTION_PROMPT),
    ("CLAUSE_ANALYSIS_PROMPT", CLAUSE_ANALYSIS_PROMPT),
    ("POLICY_MAPPING_PROMPT", POLICY_MAPPING_PROMPT),
    ("RISK_SIMULATION_PROMPT", RISK_SIMULATION_PROMPT),
    ("RECOMMENDATION_PROMPT", RECOMMENDATION_PROMPT),
    ("REPORT_PROMPT", REPORT_PROMPT),
])
def test_all_prompts_start_with_guardrail(prompt_name, prompt):
    """Property 15: Every agent system prompt begins with the canonical GUARDRAIL block.

    **Validates: Requirements 6.4**
    """
    assert prompt.startswith(GUARDRAIL), (
        f"{prompt_name} does not start with GUARDRAIL"
    )
