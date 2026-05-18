"""POST /api/analyze — run the LangGraph pipeline (Req 2.1, 2.8, 2.9, 8.2).

Accepts a JSON body with a ``job_id`` that was previously created by
``POST /api/upload``.  Retrieves the stored contract and policy content,
invokes the compiled LangGraph graph, persists the resulting
``GovernanceReport``, and returns it as JSON.

Error handling:
  - 404 if the job does not exist (Req 8.2).
  - 502 if any agent produces invalid output after the repair retry (Req 6.3).
  - 502 for any other unexpected agent failure.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import job_store
from app.agents.graph import build_graph
from app.agents.gemini_client import GeminiValidationError

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""

    job_id: str
    """UUID of the analysis job created by POST /api/upload."""


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Invoke the full LangGraph pipeline for the given job.

    Retrieves the contract and policy content from the job store, builds
    and runs the compiled graph, then persists the resulting report.

    Returns:
        The serialised ``GovernanceReport`` as a JSON object.

    Raises:
        HTTPException 404: If ``job_id`` is not found in the job store.
        HTTPException 502: If an agent produces invalid output (Req 6.3)
            or raises an unexpected exception.
    """
    job = job_store.get(req.job_id)
    if job is None:
        raise HTTPException(
            404,
            {
                "error_code": "JOB_NOT_FOUND",
                "message": f"Job {req.job_id} not found",
            },
        )

    initial_state = {
        "job_id": req.job_id,
        "contract_text": job.get("contract_text", ""),
        "contract_bytes": job.get("contract_bytes", b""),
        "policy_text": job.get("policy_text", ""),
        "audit_entries": [],
    }

    try:
        graph = build_graph()
        final_state = graph.invoke(initial_state)
    except GeminiValidationError as e:
        raise HTTPException(
            502,
            {
                "error_code": "AGENT_OUTPUT_INVALID",
                "agent": e.agent_name,
                "message": e.validation_error,
            },
        )
    except Exception as e:
        agent_name = getattr(e, "agent_name", "unknown")
        raise HTTPException(
            502,
            {
                "error_code": "AGENT_FAILURE",
                "agent": agent_name,
                "job_id": req.job_id,
                "message": str(e),
            },
        )

    report = final_state.get("report", {})

    # Persist the completed report and detected language (Req 2.9)
    job_store.put(req.job_id, report=report, language=final_state.get("language", "en"))

    return report
