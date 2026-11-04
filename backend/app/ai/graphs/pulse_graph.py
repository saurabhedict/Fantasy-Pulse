"""LangGraph pipeline for the per-over explanation.

START -> build_context -> (big swing? -> flag_big_swing) -> explain -> END
"""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.explain import explain
from app.domain.context import build_context


class PulseState(TypedDict, total=False):
    balls: list
    tl: list
    step: int
    xi: list
    captain: str
    vc: str
    max_overs: int
    threshold: float
    llms: Any
    ctx: dict
    explanation: str
    source: str
    provider: str | None


def _n_context(state):
    return {"ctx": build_context(state["balls"], state["tl"], state["step"], state["xi"],
                                 state["captain"], state["vc"], state.get("max_overs", 20))}


def _route(state):
    return "flag" if abs(state["ctx"]["fan_delta"]) >= state.get("threshold", 20.0) else "explain"


def _n_flag(state):
    return {"ctx": {**state["ctx"], "big_swing": True}}


def _n_explain(state):
    text, source, provider = explain(state["ctx"], state.get("llms"))
    return {"explanation": text, "source": source, "provider": provider}


def build_pulse_graph():
    g = StateGraph(PulseState)
    g.add_node("build_context", _n_context)
    g.add_node("flag_big_swing", _n_flag)
    g.add_node("explain", _n_explain)
    g.add_edge(START, "build_context")
    g.add_conditional_edges("build_context", _route, {"flag": "flag_big_swing", "explain": "explain"})
    g.add_edge("flag_big_swing", "explain")
    g.add_edge("explain", END)
    return g.compile()


_GRAPH = None


def run_pulse(*, balls, tl, step, xi, captain, vc, max_overs, llms, threshold=20.0) -> dict:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_pulse_graph()
    return _GRAPH.invoke({"balls": balls, "tl": tl, "step": step, "xi": xi, "captain": captain, "vc": vc,
                          "max_overs": max_overs, "threshold": threshold, "llms": llms})