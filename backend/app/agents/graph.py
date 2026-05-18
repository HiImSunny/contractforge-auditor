"""
LangGraph pipeline wiring for ContractForge Auditor.

This module assembles the six agent nodes into a compiled LangGraph pipeline
(Req 2.1, 2.2).  The pipeline runs sequentially:

    ingestion → clause_analysis → policy_mapping
              → risk_simulation → recommendation → report

Usage
-----
Build and invoke the compiled graph::

    from app.agents.graph import build_graph

    graph = build_graph()
    result_state = graph.invoke(initial_state)

``build_graph()`` returns a compiled ``StateGraph`` that accepts a
``PipelineState`` dict as its initial state and returns the fully-populated
``PipelineState`` after all nodes have executed.
"""

from langgraph.graph import StateGraph, END

from .state import PipelineState
from . import ingestion, clause_analysis, policy_mapping
from . import risk_simulation, recommendation, report


def build_graph():
    """Construct and compile the ContractForge Auditor LangGraph pipeline.

    Registers all six agent nodes and wires them in the fixed sequential
    order required by the design (Req 2.1, 2.2), then compiles the graph
    so it can be invoked directly.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph graph.  Invoke it with::

            graph.invoke(initial_state)

        where ``initial_state`` is a ``PipelineState`` dict containing at
        minimum ``job_id``, ``contract_text``, and ``policy_text``.
    """
    g = StateGraph(PipelineState)

    g.add_node("ingestion",       ingestion.run)
    g.add_node("clause_analysis", clause_analysis.run)
    g.add_node("policy_mapping",  policy_mapping.run)
    g.add_node("risk_simulation", risk_simulation.run)
    g.add_node("recommendation",  recommendation.run)
    g.add_node("report",          report.run)

    g.set_entry_point("ingestion")
    g.add_edge("ingestion",       "clause_analysis")
    g.add_edge("clause_analysis", "policy_mapping")
    g.add_edge("policy_mapping",  "risk_simulation")
    g.add_edge("risk_simulation", "recommendation")
    g.add_edge("recommendation",  "report")
    g.add_edge("report",          END)

    return g.compile()
