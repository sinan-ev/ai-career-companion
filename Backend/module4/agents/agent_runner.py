import uuid #Universally Unique Identifier(Unique execution ID for each run)
from typing import List, Dict, Any, Optional
from agents.agent_graph import PIPELINE, AgentState

def run_pipeline(data: List[Dict[str, Any]], target_column: str, date_column: Optional[str] = None, problem: str = "Full analysis") -> Dict[str, Any]:
    """
    Executes the comprehensive agentic analysis pipeline over a tabular dataset.

    Initializes the shared workflow state with tracking UUIDs, then invokes the LangGraph
    state engine to run prediction, forecasting, explainability, risk, and report nodes.

    Args:
        data (List[Dict[str, Any]]): The tabular dataset represented as a list of dictionaries (records).
        target_column (str): The column of interest to analyze or predict.
        date_column (Optional[str], optional): The column representing time coordinates, if time-series analysis is desired. Defaults to None.
        problem (str, optional): A text explanation of the target domain/problem. Defaults to "Full analysis".

    Returns:
        Dict[str, Any]: The finalized agent workspace state containing all outputs, scores, and markdown reports.
    """
    initial_state: AgentState = {
        "data": data,
        "target_column": target_column,
        "date_column": date_column,
        "problem": problem,
        "job_id": str(uuid.uuid4()),
        "prediction_result": None,
        "forecast_result": None,
        "rca_result": None,
        "risk_result": None,
        "recommendation_result": None,
        "decision_result": None,
        "overall_confidence": None,
        "final_report": None,
        "errors": []
    }
    
    final_state = PIPELINE.invoke(initial_state)
    return final_state
