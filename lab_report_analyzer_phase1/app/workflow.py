"""Validation/review routing, using LangGraph when installed with a deterministic fallback."""
from typing import TypedDict
from .schemas import ReportAnalysis
from .guardrails import validate_analysis

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:  # Keep the basic app usable when optional orchestration deps aren't installed.
    StateGraph = START = END = None
    LANGGRAPH_AVAILABLE = False

class AnalysisState(TypedDict, total=False):
    analysis: ReportAnalysis
    route: str

def validate_node(state: AnalysisState) -> AnalysisState:
    return {"analysis": validate_analysis(state["analysis"])}

def review_gate_node(state: AnalysisState) -> AnalysisState:
    a = state["analysis"]
    needs_review = a.needs_human_review or bool(a.warnings) or any(
        r.extraction_status != "extracted" for r in a.results
    )
    return {"route": "human_review" if needs_review else "complete"}

def build_analysis_graph():
    if not LANGGRAPH_AVAILABLE:
        return None
    graph = StateGraph(AnalysisState)
    graph.add_node("validate", validate_node)
    graph.add_node("review_gate", review_gate_node)
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "review_gate")
    graph.add_conditional_edges("review_gate", lambda s: s["route"], {
        "human_review": END,
        "complete": END,
    })
    return graph.compile()

analysis_graph = build_analysis_graph()

def run_guarded_analysis(analysis: ReportAnalysis) -> ReportAnalysis:
    if analysis_graph is None:
        return validate_analysis(analysis)
    result = analysis_graph.invoke({"analysis": analysis})
    return result["analysis"]
