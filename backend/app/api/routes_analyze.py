"""POST /api/analyze — run the LangGraph pipeline (Req 2.1, 2.8, 2.9, 8.2).

Accepts a JSON body with a ``job_id`` that was previously created by
``POST /api/upload``.  Kicks off the pipeline in a background thread and
returns immediately with ``{"status": "processing"}``.

GET /api/analyze/stream/{job_id} — SSE endpoint that streams agent progress
events in real-time as each node completes.

GET /api/analyze/status/{job_id} — polling fallback for environments that
don't support SSE.
"""
import json
import logging
import threading
from queue import Empty

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import job_store
from app.agents.graph import build_graph
from app.agents.gemini_client import GeminiValidationError

logger = logging.getLogger(__name__)
router = APIRouter()

AGENT_ORDER = [
    "ingestion",
    "clause_analysis",
    "policy_mapping",
    "risk_simulation",
    "recommendation",
    "report_gen",
]


class AnalyzeRequest(BaseModel):
    job_id: str


# ── Pipeline wrapper that emits SSE events per agent ─────────────────────────

def _wrap_node(original_fn, agent_name: str, job_id: str):
    """Wrap a LangGraph node function to emit SSE events before/after."""
    def wrapped(state):
        job_store.push_event(job_id, "agent_start", json.dumps({"agent": agent_name}))
        result = original_fn(state)
        job_store.push_event(job_id, "agent_done",  json.dumps({"agent": agent_name}))
        return result
    return wrapped


def _run_pipeline(job_id: str) -> None:
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
        # Import agent modules to wrap them
        from app.agents import (
            ingestion, clause_analysis, policy_mapping,
            risk_simulation, recommendation, report,
        )
        from langgraph.graph import StateGraph, END
        from app.agents.state import PipelineState

        g = StateGraph(PipelineState)
        g.add_node("ingestion",       _wrap_node(ingestion.run,       "ingestion",       job_id))
        g.add_node("clause_analysis", _wrap_node(clause_analysis.run, "clause_analysis", job_id))
        g.add_node("policy_mapping",  _wrap_node(policy_mapping.run,  "policy_mapping",  job_id))
        g.add_node("risk_simulation", _wrap_node(risk_simulation.run, "risk_simulation", job_id))
        g.add_node("recommendation",  _wrap_node(recommendation.run,  "recommendation",  job_id))
        g.add_node("report_gen",      _wrap_node(report.run,          "report_gen",      job_id))
        g.set_entry_point("ingestion")
        g.add_edge("ingestion",       "clause_analysis")
        g.add_edge("clause_analysis", "policy_mapping")
        g.add_edge("policy_mapping",  "risk_simulation")
        g.add_edge("risk_simulation", "recommendation")
        g.add_edge("recommendation",  "report_gen")
        g.add_edge("report_gen",      END)
        graph = g.compile()

        final_state = graph.invoke(initial_state)
        result_report = final_state.get("report", {})
        if not result_report:
            logger.error("Pipeline completed but report is empty for job %s. State keys: %s",
                         job_id, list(final_state.keys()))

        job_store.put(
            job_id,
            report=result_report,
            language=final_state.get("language", "en"),
            pipeline_status="done",
            pipeline_error=None,
        )
        job_store.push_event(job_id, "done", json.dumps({"status": "done"}))
        logger.info("Pipeline completed for job %s, report keys: %s",
                    job_id, list(result_report.keys()) if result_report else [])

    except GeminiValidationError as e:
        logger.error("AGENT_OUTPUT_INVALID job=%s agent=%s error=%s",
                     job_id, e.agent_name, e.validation_error)
        err = {"error_code": "AGENT_OUTPUT_INVALID", "agent": e.agent_name, "message": e.validation_error}
        job_store.put(job_id, pipeline_status="error", pipeline_error=err)
        job_store.push_event(job_id, "error", json.dumps(err))

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("AGENT_FAILURE job=%s agent=%s error=%s\n%s",
                     job_id, getattr(e, "agent_name", "unknown"), str(e), tb)
        err = {"error_code": "AGENT_FAILURE", "agent": getattr(e, "agent_name", "unknown"), "message": str(e)}
        job_store.put(job_id, pipeline_status="error", pipeline_error={"traceback": tb, **err})
        job_store.push_event(job_id, "error", json.dumps(err))

    finally:
        job_store.close_stream(job_id)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    job = job_store.get(req.job_id)
    if job is None:
        raise HTTPException(404, {"error_code": "JOB_NOT_FOUND", "message": f"Job {req.job_id} not found"})

    if job.get("pipeline_status") == "processing":
        raise HTTPException(409, {"error_code": "ALREADY_PROCESSING", "message": "Pipeline already running"})

    job_store.put(req.job_id, pipeline_status="processing", pipeline_error=None)
    threading.Thread(target=_run_pipeline, args=(req.job_id,), daemon=True).start()
    return {"status": "processing", "job_id": req.job_id}


@router.get("/analyze/stream/{job_id}")
async def analyze_stream(job_id: str, request: Request):
    """SSE endpoint — streams agent_start / agent_done / done / error events."""
    if not job_store.exists(job_id):
        raise HTTPException(404, {"error_code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"})

    q = job_store.subscribe(job_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = q.get(timeout=30)
                except Empty:
                    # keepalive ping
                    yield ": ping\n\n"
                    continue
                if msg is None:          # sentinel — pipeline finished
                    break
                yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
        finally:
            job_store.unsubscribe(job_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx buffering
        },
    )


@router.get("/analyze/status/{job_id}")
async def analyze_status(job_id: str):
    """Polling fallback."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(404, {"error_code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"})

    status = job.get("pipeline_status", "pending")

    if status == "done":
        return {"status": "done", "report": job.get("report", {})}

    if status == "error":
        err = dict(job.get("pipeline_error", {}))
        tb = err.pop("traceback", None)
        if tb:
            logger.error("Traceback for job %s:\n%s", job_id, tb)
        return {"status": "error", "error": err}

    return {"status": status}

