"""
Risk Simulation Agent for ContractForge Auditor.

Evaluates five fixed hypothetical risk scenarios against the extracted
contract clauses by calling the Gemini API via ``gemini_client.invoke``
and returns a partial-state dict containing ``simulations``.

References
----------
- Req 2.5  — Risk scenario simulation across five fixed scenario keys.
- Req 9.4  — Risk Simulation Agent prompt and output schema.
"""

from __future__ import annotations

import json

from app.agents import gemini_client
from app.agents.prompts import RISK_SIMULATION_PROMPT
from app.agents.schemas import SimulationResultList
from app.agents.state import PipelineState


def run(state: PipelineState) -> dict:
    """Execute the Risk Simulation Agent.

    Reads ``clauses``, ``language``, and ``job_id`` from *state*, formats the
    ``RISK_SIMULATION_PROMPT``, calls Gemini, and returns a partial-state dict
    containing ``simulations``.

    The agent always requests exactly five simulation results — one per fixed
    scenario key (``force_majeure``, ``penalty_delay``, ``data_breach``,
    ``termination``, ``payment_default``) — as enforced by the
    ``SimulationResultList`` schema.

    Parameters
    ----------
    state:
        The current LangGraph pipeline state.  Must contain:
        - ``clauses``  — list of clause dicts from the ingestion agent.
        - ``language`` — ``"en"`` or ``"vi"``.
        - ``job_id``   — UUID v4 identifying the current analysis job.

    Returns
    -------
    dict
        ``{"simulations": [<SimulationResult as dict>, ...]}``
        Always contains exactly five entries.

    Raises
    ------
    Exception
        Any exception raised by ``gemini_client.invoke`` is re-raised
        unchanged so the pipeline can handle it at the orchestration layer.
    """
    clauses: list[dict] = state["clauses"]
    language: str = state["language"]
    job_id: str = state["job_id"]

    prompt = RISK_SIMULATION_PROMPT.format(
        language=language,
        clauses_json=json.dumps(clauses, ensure_ascii=False),
    )

    result: SimulationResultList = gemini_client.invoke(
        prompt,
        SimulationResultList,
        "risk_simulation",
        job_id,
    )

    return {"simulations": [s.model_dump() for s in result.simulations]}
