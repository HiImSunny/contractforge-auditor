"""Audit trail persistence (Req 5.1, 5.2, 5.3, 5.5).

Each agent invocation produces an AuditEntry that is appended to the
job-scoped list in the in-memory job store.  The list is returned in
chronological order by list_for_job, satisfying Req 5.2 and 5.6.
"""
from pydantic import BaseModel
from app.services import job_store


class AuditEntry(BaseModel):
    job_id: str
    agent_name: str
    input_sha256: str   # 64 hex chars
    output_sha256: str  # 64 hex chars (or "" on failure)
    timestamp_iso8601: str
    model_version: str
    latency_ms: int


def record(entry: AuditEntry) -> None:
    """Persist an AuditEntry to the job store."""
    job_store.append_audit(entry.job_id, entry.model_dump())


def list_for_job(job_id: str) -> list[dict]:
    """Return all AuditEntry dicts for job_id in chronological order."""
    job = job_store.get(job_id)
    if job is None:
        return []
    return list(job.get("audit_entries", []))
