from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class ConfidenceScore(BaseModel):
    """
    Structured representation of the confidence evaluation of an engine run.

    Attributes:
        score (float): Numeric value ranging from 0.0 to 1.0.
        level (str): Category name representing confidence (e.g., 'very high', 'high', 'moderate', 'low', 'uncertain').
        explanation (str): A concise, single-sentence reason justifying the confidence level.
        basis (List[str]): List of individual components and factors that contributed to the confidence score.
        suggestions (List[str]): Actionable suggestions to improve prediction/model confidence.
    """
    score: float = Field(..., ge=0.0, le=1.0, description="0.0 - 1.0")
    level: str = Field(..., description="very high / high / moderate / low / uncertain")
    explanation: str = Field(..., description="1-sentence plain English reason")
    basis: List[str] = Field(..., description="list of factors that produced this score")
    suggestions: List[str] = Field(..., min_length=1, description="at least 1 suggestion to improve confidence")

class PredictionRequest(BaseModel):
    """
    Schema representing the request payload for predicting a target column.

    Attributes:
        data (List[Dict[str, Any]]): The list of records to predict on.
        target_column (str): The name of the target column to predict.
    """
    data: List[Dict[str, Any]]
    target_column: str

class ForecastRequest(BaseModel):
    """
    Schema representing the request payload for running a forecast analysis.

    Attributes:
        data (List[Dict[str, Any]]): The input timeseries data points.
        date_column (str): The column containing timestamps or dates.
        value_column (str): The column containing numerical target values to forecast.
        periods (int, optional): The number of periods to forecast ahead. Defaults to 6.
    """
    data: List[Dict[str, Any]]
    date_column: str
    value_column: str
    periods: int = 6

class RCARequest(BaseModel):
    """
    Schema representing the request payload for Root Cause Analysis (RCA).

    Attributes:
        data (List[Dict[str, Any]]): The dataset containing potential causative features.
        target_column (str): The main target feature column.
        problem (str): Description of the observed business issue or behavior.
    """
    data: List[Dict[str, Any]]
    target_column: str
    problem: str

class RiskRequest(BaseModel):
    """
    Schema representing the request payload for Risk and Anomaly Assessment.

    Attributes:
        data (List[Dict[str, Any]]): The list of records to assess for risks and anomalies.
    """
    data: List[Dict[str, Any]]

class RecommendRequest(BaseModel):
    """
    Schema representing the request payload for generating prescriptive recommendations.

    Attributes:
        insights (List[str]): Insights generated from analysis engines.
        prediction_confidence (float): The confidence score of the predictive model.
        risk_score (float): The computed risk score from the risk engine.
        top_risk_features (List[str]): Features identified as driving the risk.
    """
    insights: List[str]
    prediction_confidence: float
    risk_score: float
    top_risk_features: List[str]

class DecisionRequest(BaseModel):
    """
    Schema representing the request payload for a single decision intelligence run.

    Attributes:
        data (List[Dict[str, Any]]): The records representing the business situation.
        target_column (str): The primary outcome feature column.
        date_column (str, optional): The optional date column for temporal reasoning. Defaults to None.
        problem (str, optional): The business challenge or decision problem to address. Defaults to "Analyse this dataset".
    """
    data: List[Dict[str, Any]]
    target_column: str
    date_column: Optional[str] = None
    problem: str = "Analyse this dataset"

class AgentRunRequest(BaseModel):
    """
    Schema representing the request payload to initiate a full decision agent run.

    Attributes:
        data (List[Dict[str, Any]]): The complete dataset to run through all analysis stages.
        target_column (str): The primary outcome feature column to inspect.
        date_column (str, optional): The optional date column for timeseries capabilities. Defaults to None.
        problem (str, optional): The high-level objective/problem description. Defaults to "Full pipeline analysis".
    """
    data: List[Dict[str, Any]]
    target_column: str
    date_column: Optional[str] = None
    problem: str = "Full pipeline analysis"

class PredictionResponse(BaseModel):
    """
    Schema representing the response payload of a prediction task.

    Attributes:
        task_type (str): Classification or regression classification.
        domain (str, optional): The domain name (e.g., General, Healthcare). Defaults to "General".
        model_used (str): The model algorithm name used for predictions.
        cv_score (float): Cross-validation score of the trained model.
        predictions (List[Dict[str, Any]]): List of generated prediction values.
        metrics (Dict[str, float]): Evaluated performance metrics.
        class_distribution (List[Dict[str, Any]], optional): Distribution counts/frequencies for classes. Defaults to None.
        business_summary (str, optional): Executive summary of predictions. Defaults to None.
        confidence (ConfidenceScore): Confidence evaluation of the predictive model.
    """
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
    """
    Schema representing the response payload of a forecasting run.

    Attributes:
        model_used (str): The model algorithm used for forecasting.
        forecast (List[Dict[str, Any]]): Projected timeseries data points.
        trend_direction (str): Identified trend direction (e.g., 'upward', 'downward', 'flat').
        trend_explanation (str): Text explanation of the projected trend.
        confidence (ConfidenceScore): Confidence evaluation of the forecast.
    """
    model_config = ConfigDict(protected_namespaces=())
    model_used: str
    forecast: List[Dict[str, Any]]
    trend_direction: str
    trend_explanation: str
    confidence: ConfidenceScore

class RCAResponse(BaseModel):
    """
    Schema representing the response payload of a root cause analysis run.

    Attributes:
        top_features (List[Dict[str, Any]]): List of features sorted by SHAP/influence values.
        causal_chain (List[str]): Sequence of key attributes leading to the outcome.
        explanation (str): Plain-English root cause description.
        confidence (ConfidenceScore): Confidence evaluation of the RCA model.
    """
    top_features: List[Dict[str, Any]]
    causal_chain: List[str]
    explanation: str
    confidence: ConfidenceScore

class RiskResponse(BaseModel):
    """
    Schema representing the response payload of a risk assessment run.

    Attributes:
        total_records (int): Total count of processed rows.
        anomaly_count (int): Count of anomalous/high-risk records.
        anomaly_rate (float): Percentage of anomalous records detected.
        risk_score (float): Computed risk metric out of 100.
        alerts (List[str]): Warnings or alert items generated.
        anomalous_indices (List[int]): Indices of rows identified as anomalies.
        confidence (ConfidenceScore): Confidence evaluation of the risk assessment.
    """
    total_records: int
    anomaly_count: int
    anomaly_rate: float
    risk_score: float
    alerts: List[str]
    anomalous_indices: List[int]
    confidence: ConfidenceScore

class RecommendResponse(BaseModel):
    """
    Schema representing the response payload of recommendation generation.

    Attributes:
        recommendations (List[Dict[str, Any]]): Prioritized list of actionable business steps.
        confidence (ConfidenceScore): Confidence evaluation of the recommended actions.
    """
    recommendations: List[Dict[str, Any]]
    confidence: ConfidenceScore

class DecisionResponse(BaseModel):
    """
    Schema representing the response payload of the strategic decision engine.

    Attributes:
        situation (str): Description of the analyzed business scenario.
        key_finding (str): Primary data-driven finding.
        strategic_decision (str): Core recommendation or strategy selected.
        action_plan (List[str]): Recommended next execution steps.
        executive_summary (str): Summarized report for leadership.
        confidence (ConfidenceScore): Confidence evaluation of the decision logic.
    """
    situation: str
    key_finding: str
    strategic_decision: str
    action_plan: List[str]
    executive_summary: str
    confidence: ConfidenceScore

class AgentRunResponse(BaseModel):
    """
    Schema representing the response payload for a full decision agent run.

    Attributes:
        job_id (str): Unique job identifier for tracking the execution.
        prediction (PredictionResponse, optional): Prediction engine outputs. Defaults to None.
        forecast (ForecastResponse, optional): Forecasting engine outputs. Defaults to None.
        rca (RCAResponse, optional): Root cause analysis engine outputs. Defaults to None.
        risk (RiskResponse, optional): Risk assessment engine outputs. Defaults to None.
        recommendation (RecommendResponse, optional): Recommendation engine outputs. Defaults to None.
        decision (DecisionResponse, optional): Strategic decision engine outputs. Defaults to None.
        overall_confidence (ConfidenceScore): Aggregated confidence score of the entire pipeline.
        final_report (str): Formatted executive plain-text report.
        errors (List[str]): List of error messages captured during agent execution.
    """
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
    """
    Schema representing the request payload for conversational chat interaction.

    Attributes:
        message (str): The message query entered by the user.
        context (Dict[str, Any]): Active state context to provide to the chat model.
    """
    message: str
    context: Dict[str, Any]

class ChatResponse(BaseModel):
    """
    Schema representing the response payload of conversational chat.

    Attributes:
        response (str): The text response generated by the conversational assistant.
    """
    response: str
