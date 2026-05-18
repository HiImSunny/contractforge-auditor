"""
Thin Gemini wrapper used by all six ContractForge Auditor agents.

Every agent call goes through ``invoke``, which:

* Hashes the prompt and response with SHA-256 for the audit trail (Req 5.1).
* Calls the Gemini API with ``response_mime_type="application/json"`` so the
  model is constrained to emit a JSON object (Req 6.1).
* Validates the raw JSON response against the caller-supplied Pydantic v2
  ``response_model`` (Req 6.1).
* On validation failure, issues exactly one repair retry with a structured
  repair prompt that includes the original output and the validation error
  (Req 6.2).
* Writes an ``AuditEntry`` for every invocation — including validation
  failures — via ``services.audit_log`` (Req 5.1).
* Raises ``GeminiValidationError`` when both the initial call and the repair
  retry fail validation (Req 6.3).

References: Req 6.1, 6.2, 6.4, 5.1.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    pass  # avoid circular imports at runtime


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class GeminiValidationError(Exception):
    """Raised when a Gemini response fails Pydantic validation after one retry.

    Attributes:
        agent_name: The name of the agent whose output failed validation.
        validation_error: Human-readable description of the validation failure.
    """

    def __init__(self, agent_name: str, validation_error: str) -> None:
        self.agent_name = agent_name
        self.validation_error = validation_error
        super().__init__(
            f"Agent '{agent_name}' output failed validation: {validation_error}"
        )


# ---------------------------------------------------------------------------
# Audit shim
# ---------------------------------------------------------------------------


def _write_audit(
    job_id: str,
    agent_name: str,
    input_sha256: str,
    output_sha256: str,
    latency_ms: int,
) -> None:
    """Write an ``AuditEntry`` via ``services.audit_log``.

    This is a thin shim — replaced by the real ``audit_log`` in Task 4.2.
    If ``audit_log`` is not yet available the call is silently skipped so
    that the rest of the pipeline can proceed during early development.
    """
    try:
        from app.services.audit_log import record, AuditEntry  # type: ignore[import]
        import datetime

        entry = AuditEntry(
            job_id=job_id,
            agent_name=agent_name,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            timestamp_iso8601=datetime.datetime.utcnow().isoformat() + "Z",
            model_version=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            latency_ms=latency_ms,
        )
        record(entry)
    except ImportError:
        pass  # audit_log not yet available


# ---------------------------------------------------------------------------
# Repair prompt template
# ---------------------------------------------------------------------------

_REPAIR_PROMPT_TEMPLATE = """\
The following JSON response failed schema validation.

ORIGINAL PROMPT:
{original_prompt}

INVALID RESPONSE:
{invalid_response}

VALIDATION ERROR:
{validation_error}

Please return a corrected JSON response that exactly matches the required schema. No markdown, no code fences, no prose — only the JSON object.\
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    """Return the lowercase hex SHA-256 digest of *text* (64 chars)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _call_gemini(prompt: str) -> str:
    """Send *prompt* to Gemini and return the raw response text.

    Uses the model name from the ``GEMINI_MODEL`` environment variable,
    defaulting to ``"gemini-1.5-flash"``.  The ``response_mime_type`` is
    set to ``"application/json"`` so the model is constrained to emit JSON.
    """
    import google.generativeai as genai  # type: ignore[import]

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)

    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"},
    )
    response = model.generate_content(prompt)
    return response.text


def _parse_and_validate(text: str, response_model: type[BaseModel]) -> BaseModel:
    """Parse *text* as JSON and validate it against *response_model*.

    Raises:
        json.JSONDecodeError: If *text* is not valid JSON.
        pydantic.ValidationError: If the parsed JSON does not match the schema.
    """
    parsed = json.loads(text)
    return response_model.model_validate(parsed)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def invoke(
    prompt: str,
    response_model: type[BaseModel],
    agent_name: str,
    job_id: str,
) -> BaseModel:
    """Call Gemini, validate the response, and write an audit entry.

    Parameters
    ----------
    prompt:
        The full user-facing prompt (including any Anti-Injection Guardrail
        prefix) to send to Gemini.
    response_model:
        A Pydantic v2 ``BaseModel`` subclass.  The raw JSON response from
        Gemini is validated against this model before being returned.
    agent_name:
        Human-readable name of the calling agent (e.g. ``"ingestion"``).
        Used in audit entries and error messages.
    job_id:
        UUID v4 identifying the current Analysis Job.  Stored in every
        audit entry so entries can be retrieved per-job.

    Returns
    -------
    BaseModel
        The validated Pydantic model instance.

    Raises
    ------
    GeminiValidationError
        When both the initial Gemini call and the single repair retry fail
        Pydantic validation.
    """
    t0 = time.monotonic()
    input_sha256 = _sha256(prompt)

    # --- First attempt ---
    raw_response = _call_gemini(prompt)
    output_sha256 = _sha256(raw_response)
    latency_ms = int((time.monotonic() - t0) * 1000)

    try:
        validated = _parse_and_validate(raw_response, response_model)
        _write_audit(job_id, agent_name, input_sha256, output_sha256, latency_ms)
        return validated
    except (json.JSONDecodeError, ValidationError) as first_error:
        first_error_str = str(first_error)

    # --- Repair retry (Req 6.2) ---
    repair_prompt = _REPAIR_PROMPT_TEMPLATE.format(
        original_prompt=prompt,
        invalid_response=raw_response,
        validation_error=first_error_str,
    )

    t1 = time.monotonic()
    repair_input_sha256 = _sha256(repair_prompt)

    repair_response = _call_gemini(repair_prompt)
    repair_output_sha256 = _sha256(repair_response)
    repair_latency_ms = int((time.monotonic() - t1) * 1000)

    try:
        validated = _parse_and_validate(repair_response, response_model)
        _write_audit(
            job_id,
            agent_name,
            repair_input_sha256,
            repair_output_sha256,
            repair_latency_ms,
        )
        return validated
    except (json.JSONDecodeError, ValidationError) as second_error:
        second_error_str = str(second_error)

    # --- Both attempts failed — log validation failure and raise (Req 6.3, 6.5) ---
    _write_audit(
        job_id,
        f"{agent_name}:validation_failure",
        repair_input_sha256,
        repair_output_sha256,
        repair_latency_ms,
    )
    raise GeminiValidationError(agent_name, second_error_str)
