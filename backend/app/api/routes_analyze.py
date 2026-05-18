"""POST /api/analyze — run the LangGraph pipeline (Req 2.1, 2.8, 2.9, 8.2).

Accepts a JSON body with a ``job_id`` that was previously created by
``POST /api/upload``.  Kicks off the pipeline in a background thread and
returns immediately with ``{"status": "processing"}``.  The frontend polls
``GET /api/analyze/status/{job_id}`` until status is ``"done"`` or ``"error"``,
then fetches the completed report from the same endpoint.

This avoids Render's 30-second proxy timeout on free-tier deployments.

Error handling:
  - 404 if the job does not exist (Req 8.2).
  - 409 if the job is already being processed.
"""
import logging
import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import job_store
from app.agents.graph import build_graph
from app.agents.gemini_client import GeminiValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""
    job_id: str


def _run_pipeline(job_id: str) -> None:
    """Run the full LangGraph pipeline in a background thread.

    Writes ``pipeline_status`` into the job store:
      - ``"processing"`` while running
      - ``"done"``        on success  (also writes ``report`` and ``language``)
      - ``"error"``       on failure  (also writes ``pipeline_error``)
    """
    job = job_store.get(job_id)
    if job is None:
        return

    initial_state = {
        "job_id": job_id,
        "contract_text": job.get("contract_text", ""),
        "contract_bytes": job.get("contract_bytes", b""),
        "policy_text": job.get("policy_text", ""),
        "audit_entries": [],
    }

    try:
        graph = build_graph()
        final_state = graph.invoke(initial_state)
        report = final_state.get("report", {})
        if not report:
            logger.error("Pipeline completed but report is empty for job %s. State keys: %s", job_id, list(final_state.keys()))
        job_store.put(
            job_id,
            report=report,
            language=final_state.get("language", "en"),
            pipeline_status="done",
            pipeline_error=None,
        )
        logger.info("Pipeline completed for job %s, report keys: %s", job_id, list(report.keys()) if report else [])
    except GeminiValidationError as e:
        logger.error(
            "AGENT_OUTPUT_INVALID job=%s agent=%s error=%s",
            job_id, e.agent_name, e.validation_error
        )
        job_store.put(
            job_id,
            pipeline_status="error",
            pipeline_error={
                "error_code": "AGENT_OUTPUT_INVALID",
                "agent": e.agent_name,
                "message": e.validation_error,
            },
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(
            "AGENT_FAILURE job=%s agent=%s error=%s\n%s",
            job_id, getattr(e, "agent_name", "unknown"), str(e), tb
        )
        job_store.put(
            job_id,
            pipeline_status="error",
            pipeline_error={
                "error_code": "AGENT_FAILURE",
                "agent": getattr(e, "agent_name", "unknown"),
                "message": str(e),
                "traceback": tb,
            },
        )


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Kick off the LangGraph pipeline in a background thread.

    Returns immediately with ``{"status": "processing", "job_id": "..."}``.
    Poll ``GET /api/analyze/status/{job_id}`` to track progress.

    Raises:
        HTTPException 404: If ``job_id`` is not found.
        HTTPException 409: If the job is already processing or done.
    """
    job = job_store.get(req.job_id)
    if job is None:
        raise HTTPException(
            404,
            {"error_code": "JOB_NOT_FOUND", "message": f"Job {req.job_id} not found"},
        )

    current_status = job.get("pipeline_status")
    if current_status == "processing":
        raise HTTPException(
            409,
            {"error_code": "ALREADY_PROCESSING", "message": "Pipeline is already running for this job"},
        )

    # Mark as processing before spawning thread to avoid race conditions
    job_store.put(req.job_id, pipeline_status="processing", pipeline_error=None)

    thread = threading.Thread(target=_run_pipeline, args=(req.job_id,), daemon=True)
    thread.start()

    return {"status": "processing", "job_id": req.job_id}


@router.get("/analyze/status/{job_id}")
async def analyze_status(job_id: str):
    """Poll the pipeline status for a job.

    Returns:
        - ``{"status": "processing"}`` while the pipeline is running.
        - ``{"status": "done", "report": {...}}`` when complete.
        - ``{"status": "error", "error": {...}}`` on failure.

    Raises:
        HTTPException 404: If ``job_id`` is not found.
    """
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            404,
            {"error_code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"},
        )

    status = job.get("pipeline_status", "pending")

    if status == "done":
        return {"status": "done", "report": job.get("report", {})}

    if status == "error":
        err = job.get("pipeline_error", {})
        # Log traceback server-side if present, don't expose to client
        tb = err.pop("traceback", None)
        if tb:
            logger.error("Traceback for job %s:\n%s", job_id, tb)
        return {"status": "error", "error": err}

    return {"status": status}
