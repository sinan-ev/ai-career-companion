from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class ConfidenceScore(BaseModel):
    """Confidence score object."""
    score: float = Field(..., ge=0.0, le=1.0, description="0.0 - 1.0")
    level: str = Field(..., description="very high / high / moderate / low / uncertain")
    explanation: str = Field(..., description="1-sentence plain English reason")
    basis: List[str] = Field(..., description="list of factors that produced this score")
    suggestions: List[str] = Field(..., min_length=1, description="at least 1 suggestion to improve confidence")

class PredictionRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str

class ForecastRequest(BaseModel):
    data: List[Dict[str, Any]]
    date_column: str
    value_column: str
    periods: int = 6

class RCARequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    problem: str

class RiskRequest(BaseModel):
    data: List[Dict[str, Any]]

class RecommendRequest(BaseModel):
    insights: List[str]
    prediction_confidence: float
    risk_score: float
    top_risk_features: List[str]

class DecisionRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    date_column: Optional[str] = None
    problem: str = "Analyse this dataset"

class AgentRunRequest(BaseModel):
    data: List[Dict[str, Any]]
    target_column: str
    date_column: Optional[str] = None
    problem: str = "Full pipeline analysis"

class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    task_type: str
    domain: Optional[str] = "General"
    model_used: str
    cv_score: float
    predictions: List[Dict[str, Any]]
    metrics: Dict[str, float]
    class_distribution: Optional[List[Dict[str, Any]]] = None
    business_summary: Optional[str] = None
    confidence: ConfidenceScore

class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_used: str
    forecast: List[Dict[str, Any]]
    trend_direction: str
    trend_explanation: str
    confidence: ConfidenceScore

class RCAResponse(BaseModel):
    top_features: List[Dict[str, Any]]
    causal_chain: List[str]
    explanation: str
    confidence: ConfidenceScore

class RiskResponse(BaseModel):
    total_records: int
    anomaly_count: int
    anomaly_rate: float
    risk_score: float
    alerts: List[str]
    anomalous_indices: List[int]
    confidence: ConfidenceScore

class RecommendResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    confidence: ConfidenceScore

class DecisionResponse(BaseModel):
    situation: str
    key_finding: str
    strategic_decision: str
    action_plan: List[str]
    executive_summary: str
    confidence: ConfidenceScore

class AgentRunResponse(BaseModel):
    job_id: str
    prediction: Optional[PredictionResponse] = None
    forecast: Optional[ForecastResponse] = None
    rca: Optional[RCAResponse] = None
    risk: Optional[RiskResponse] = None
    recommendation: Optional[RecommendResponse] = None
    decision: Optional[DecisionResponse] = None
    overall_confidence: ConfidenceScore
    final_report: str
    errors: List[str]

class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any]

class ChatResponse(BaseModel):
    response: str
