from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
from agents.agent_definitions import (
    PredictionAgent, ForecastAgent, RCAAgent, RiskAgent,
    RecommendAgent, DecisionAgent, EvalAgent
)
from outputs.report_generator import ReportGenerator

class AgentState(TypedDict):
    data: List[Dict[str, Any]]
    target_column: str
    date_column: Optional[str]
    problem: str
    job_id: str
    prediction_result: Optional[Dict[str, Any]]
    forecast_result: Optional[Dict[str, Any]]
    rca_result: Optional[Dict[str, Any]]
    risk_result: Optional[Dict[str, Any]]
    recommendation_result: Optional[Dict[str, Any]]
    decision_result: Optional[Dict[str, Any]]
    overall_confidence: Optional[Dict[str, Any]]
    final_report: Optional[str]
    errors: List[str]

class ReportNode:
    def run(self, state: dict) -> dict:
        try:
            generator = ReportGenerator()
            report = generator.generate(state)
            state["final_report"] = report
        except Exception as e:
            state["errors"].append(f"ReportNode error: {str(e)}")
            state["final_report"] = "Failed to generate report."
        return state

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("prediction", lambda s: PredictionAgent().run(s))
    graph.add_node("forecast", lambda s: ForecastAgent().run(s))
    graph.add_node("rca", lambda s: RCAAgent().run(s))
    graph.add_node("risk", lambda s: RiskAgent().run(s))
    graph.add_node("recommend", lambda s: RecommendAgent().run(s))
    graph.add_node("decision", lambda s: DecisionAgent().run(s))
    graph.add_node("eval", lambda s: EvalAgent().run(s))
    graph.add_node("report", lambda s: ReportNode().run(s))

    graph.add_edge(START, "prediction")
    graph.add_edge("prediction", "forecast")
    graph.add_edge("forecast", "rca")
    graph.add_edge("rca", "risk")
    graph.add_edge("risk", "recommend")
    graph.add_edge("recommend", "decision")
    graph.add_edge("decision", "eval")
    graph.add_edge("eval", "report")
    graph.add_edge("report", END)

    return graph.compile()

PIPELINE = build_graph()
