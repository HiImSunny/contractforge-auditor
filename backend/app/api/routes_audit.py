"""GET /api/audit-trail/{job_id} — return audit entries (Req 5.2, 5.3, 8.5).

Returns the ordered list of ``AuditEntry`` dicts for the given job.  Each
entry records the agent name, SHA-256 hashes of the input prompt and output
response, timestamp, model version, and latency (Req 5.1, 5.2).

The entries are returned in chronological order (Req 5.2, 5.6).

Error handling:
  - 404 if the job does not exist.
"""
from fastapi import APIRouter, HTTPException

from app.services import audit_log, job_store

router = APIRouter()


@router.get("/audit-trail/{job_id}")
async def get_audit_trail(job_id: str):
    """Return all audit entries for the given job in chronological order.

    Retrieves the ordered list of ``AuditEntry`` dicts stored against
    ``job_id`` in the job store (Req 5.2, 5.3).

    Args:
        job_id: UUID of the analysis job.

    Returns:
        A JSON array of ``AuditEntry`` dicts, ordered by invocation time.

    Raises:
        HTTPException 404: If ``job_id`` is not found in the job store.
    """
    if not job_store.exists(job_id):
        raise HTTPException(
            404,
            {
                "error_code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} not found",
            },
        )
    return audit_log.list_for_job(job_id)
