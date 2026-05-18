"""POST /api/simulate — return a specific simulation result (Req 8.3, 8.7).

Accepts a JSON body with a ``job_id`` and a ``scenario_key``.  Looks up the
completed ``GovernanceReport`` for the job and returns the
``SimulationResult`` matching the requested scenario.

Valid scenario keys (Req 2.6):
  ``force_majeure``, ``penalty_delay``, ``data_breach``,
  ``termination``, ``payment_default``

Error handling:
  - 400 if ``scenario_key`` is not one of the five valid values.
  - 404 if the job does not exist.
  - 409 if the analysis has not yet completed (no report stored).
  - 404 if the scenario is not present in the stored report.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import job_store

router = APIRouter()

VALID_SCENARIOS = {
    "force_majeure",
    "penalty_delay",
    "data_breach",
    "termination",
    "payment_default",
}


class SimulateRequest(BaseModel):
    """Request body for the /api/simulate endpoint."""

    job_id: str
    """UUID of the analysis job created by POST /api/upload."""

    scenario_key: str
    """One of the five fixed risk-scenario identifiers (Req 2.6)."""


@router.post("/simulate")
async def simulate(req: SimulateRequest):
    """Return the simulation result for a specific scenario and job.

    Validates the scenario key, retrieves the stored report, and returns
    the matching ``SimulationResult`` dict.

    Returns:
        The ``SimulationResult`` dict for the requested scenario.

    Raises:
        HTTPException 400: If ``scenario_key`` is not a recognised value.
        HTTPException 404: If the job is not found.
        HTTPException 409: If the analysis report is not yet available.
        HTTPException 404: If the scenario is not present in the report.
    """
    if req.scenario_key not in VALID_SCENARIOS:
        raise HTTPException(
            400,
            {
                "error_code": "UNKNOWN_SCENARIO",
                "message": f"Unknown scenario: {req.scenario_key}",
            },
        )

    job = job_store.get(req.job_id)
    if job is None:
        raise HTTPException(
            404,
            {
                "error_code": "JOB_NOT_FOUND",
                "message": f"Job {req.job_id} not found",
            },
        )

    report = job.get("report")
    if not report:
        raise HTTPException(
            409,
            {
                "error_code": "REPORT_NOT_READY",
                "message": "Analysis not yet complete",
            },
        )

    simulations = report.get("simulations", [])
    for sim in simulations:
        if sim.get("scenario_key") == req.scenario_key:
            return sim

    raise HTTPException(
        404,
        {
            "error_code": "SCENARIO_NOT_FOUND",
            "message": f"Scenario {req.scenario_key} not found in report",
        },
    )
