from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
from agents.agent_definitions import (
    PredictionAgent, ForecastAgent, RCAAgent, RiskAgent,
    RecommendAgent, DecisionAgent, EvalAgent
)
from outputs.report_generator import ReportGenerator

class AgentState(TypedDict):
    """
    TypedDict representing the shared workspace state managed throughout the LangGraph workflow.

    Attributes:
        data (List[Dict[str, Any]]): The active tabular dataset loaded as list of records.
        target_column (str): The name of the prediction target column.
        date_column (Optional[str]): The datetime/time series column, if any exists.
        problem (str): Description of the analytical problem domain.
        job_id (str): Generated UUID tracking this specific pipeline job execution.
        prediction_result (Optional[Dict[str, Any]]): Outputs calculated by the PredictionAgent.
        forecast_result (Optional[Dict[str, Any]]): Outputs calculated by the ForecastAgent.
        rca_result (Optional[Dict[str, Any]]): Outputs calculated by the RCAAgent.
        risk_result (Optional[Dict[str, Any]]): Outputs calculated by the RiskAgent.
        recommendation_result (Optional[Dict[str, Any]]): Outputs calculated by the RecommendAgent.
        decision_result (Optional[Dict[str, Any]]): Outputs calculated by the DecisionAgent.
        overall_confidence (Optional[Dict[str, Any]]): Scoring calculated by the EvalAgent.
        final_report (Optional[str]): Consolidated executive report calculated by the ReportNode.
        errors (List[str]): List of warning and error strings logged during pipeline run.
    """
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
    """
     LangGraph node wrapper that triggers compilation of the final executive report.
    """
    def run(self, state: dict) -> dict:
        """
        Executes report generation from current state metrics.

        Args:
            state (dict): Shared workflow state dictionary.

        Returns:
            dict: Updated state containing the markdown final report.
        """
        try:
            generator = ReportGenerator()
            report = generator.generate(state)
            state["final_report"] = report
        except Exception as e:
            state["errors"].append(f"ReportNode error: {str(e)}")
            state["final_report"] = "Failed to generate report."
        return state

def build_graph():
    """
    Compiles the sequential StateGraph connecting all analysis agents to one another.

    Flow: START → Prediction → Forecast → RCA → Risk → Recommend → Decision → Eval → Report → END

    Returns:
        CompiledStateGraph: The runnable LangGraph state workflow object.
    """
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
