import uuid
from typing import List, Dict, Any, Optional
from agents.agent_graph import PIPELINE, AgentState

def run_pipeline(data: List[Dict[str, Any]], target_column: str, date_column: Optional[str] = None, problem: str = "Full analysis") -> Dict[str, Any]:
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
