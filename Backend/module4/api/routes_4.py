from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import pandas as pd
from schemas.models import *
from engines.prediction_engine import PredictionEngine
from engines.forecasting_engine import ForecastingEngine
from engines.rca_agent import RCAAgent
from engines.risk_engine import RiskEngine
from engines.recommendation_engine import RecommendationEngine
from engines.decision_engine import DecisionEngine
from engines.chat_agent import ChatAgent
from agents.agent_runner import run_pipeline
from explainability.xai_layer import XAILayer
from monitoring.model_monitor import ModelMonitor
from outputs.report_generator import ReportGenerator
from ingestion.data_router import validate_dataset, route_data
import numpy as np

def sanitize_json(data):
    """
    Recursively replaces non-JSON compliant floats (NaN, Inf, -Inf) with 0.0.

    Args:
        data (any): The dictionary, list, float, or other data to sanitize.

    Returns:
        any: JSON-compliant representation of the input.
    """
    if isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(v) for v in data]
    elif isinstance(data, float):
        if not np.isfinite(data):
            return 0.0
        return data
    else:
        return data

app = FastAPI(
    title="Module 4 — AI Decision Intelligence",
    description="Prediction · Forecasting · RCA · Risk · Recommendations · Decisions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

monitor = ModelMonitor()

@app.get("/")
async def root():
    """
    Serves the root landing endpoint for the Module 4 API.

    Returns:
        dict: Welcome message, version info, and lists of available API routes.
    """
    return {
        "message": "Module 4 is running",
        "version": "1.0.0",
        "module": "4",
        "status": "ok",
        "available_routes": [
            "/health", "/predict", "/forecast", "/rca", "/risk",
            "/recommend", "/decide", "/run-pipeline", "/pipeline-status",
            "/explain", "/monitor", "/monitor/drift", "/chat"
        ]
    }

@app.get("/health")
async def health():
    """
    Retrieves system health status including enabled engines and active monitoring reports.

    Returns:
        dict: Health status dictionary.
    """
    return {
        "status": "ok",
        "module": "4",
        "port": 8004,
        "engines": ["prediction", "forecasting", "rca", "risk", "recommendation", "decision", "agents"],
        "monitor": monitor.get_health_report()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Triggers prediction model training and inference on the uploaded dataset.

    Args:
        request (PredictionRequest): Pydantic model carrying data and target column name.

    Returns:
        PredictionResponse: Metrics, confidence scores, and predicted values.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        engine = PredictionEngine()
        result = engine.train_and_predict(request.data, request.target_column)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("predict", result.get("metrics", {}), conf_score, "PredictionEngine")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    """
    Generates time-series predictions/forecasts for numeric values over date records.

    Args:
        request (ForecastRequest): Pydantic model carrying dataset, date column, value column, and steps.

    Returns:
        ForecastResponse: Generated future projections and interval confidence scores.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        engine = ForecastingEngine()
        result = engine.forecast(request.data, request.date_column, request.value_column, request.periods)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("forecast", {"periods": request.periods}, conf_score, "ForecastingEngine")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.post("/rca", response_model=RCAResponse)
async def rca(request: RCARequest):
    """
    Runs explainability analysis (SHAP / Feature Importance) to identify predictive drivers.

    Args:
        request (RCARequest): Pydantic model carrying data, target column, and core business problem statement.

    Returns:
        RCAResponse: Identified key features, impact scores, and structured confidence info.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        agent = RCAAgent()
        result = agent.analyse(request.data, request.target_column, request.problem)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("rca", {"top_features_count": len(result.get("top_features", []))}, conf_score, "RCAAgent")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.post("/risk", response_model=RiskResponse)
async def risk(request: RiskRequest):
    """
    Scours dataset records for anomalies, outliers, and data corruption metrics.

    Args:
        request (RiskRequest): Pydantic model containing data records.

    Returns:
        RiskResponse: Computed anomalies list and numerical risk scores.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        engine = RiskEngine()
        result = engine.detect(request.data)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("risk", {"risk_score": result.get("risk_score")}, conf_score, "RiskEngine")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    Synthesizes prediction statistics and risks to construct prioritized actionable insights.

    Args:
        request (RecommendRequest): Pydantic model containing insights, prediction, and risk score metrics.

    Returns:
        RecommendResponse: Ranked executive actions list.
    """
    try:
        engine = RecommendationEngine()
        result = engine.recommend(request.insights, request.prediction_confidence, request.risk_score, request.top_risk_features)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("recommend", {"recs_count": len(result.get("recommendations", []))}, conf_score, "RecommendationEngine")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input values"})

@app.post("/decide", response_model=DecisionResponse)
async def decide(request: DecisionRequest):
    """
    Runs full analysis workflow synchronously to render executive-level strategic decisions.

    Args:
        request (DecisionRequest): Pydantic model containing records and analytical scope.

    Returns:
        DecisionResponse: Strategic decree, threat level assessment, and confidence insights.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        # Run dependencies
        pred_engine = PredictionEngine()
        pred_res = pred_engine.train_and_predict(request.data, request.target_column)
        
        rca_engine = RCAAgent()
        rca_res = rca_engine.analyse(request.data, request.target_column, request.problem)
        
        risk_engine = RiskEngine()
        risk_res = risk_engine.detect(request.data)
        
        rec_engine = RecommendationEngine()
        top_features = [f["feature"] for f in rca_res.get("top_features", [])]
        pred_conf = pred_res.get("confidence", {}).get("score", 0.0)
        risk_score = risk_res.get("risk_score", 0.0)
        rec_res = rec_engine.recommend([], pred_conf, risk_score, top_features)
        
        engine = DecisionEngine()
        result = engine.decide(pred_res, None, rca_res, risk_res, rec_res)
        
        conf_score = result.get("confidence", {}).get("score", 0.0)
        monitor.log_run("decide", {}, conf_score, "DecisionEngine")
        
        return sanitize_json(result)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.post("/chat", response_model=ChatResponse)
async def chat_with_future_intelligence(request: ChatRequest):
    """
    Serves as conversational portal directly engaging with Module 4 Future Intelligence Core.

    Args:
        request (ChatRequest): Pydantic model containing user prompt and active execution state.

    Returns:
        ChatResponse: Structured response text.
    """
    try:
        agent = ChatAgent()
        response_text = agent.chat(request.message, request.context)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "chat_failed", "message": str(e)})

@app.post("/run-pipeline", response_model=AgentRunResponse)
async def run_pipeline_endpoint(request: AgentRunRequest):
    """
    Invokes the multi-agent decision intelligence pipeline in LangGraph and generates unified reports.

    Args:
        request (AgentRunRequest): Pydantic model detailing the tabular dataset and analytical configurations.

    Returns:
        AgentRunResponse: Fully structured payload carrying prediction, forecast, risk, decision, and report metrics.
    """
    try:
        df = pd.DataFrame(request.data)
        is_valid, msg = validate_dataset(df)
        if not is_valid:
            raise ValueError(msg)
            
        final_state = run_pipeline(request.data, request.target_column, request.date_column, request.problem)
        
        overall_conf = final_state.get("overall_confidence", {}).get("score", 0.0)
        monitor.log_run("run-pipeline", {"job_id": final_state.get("job_id")}, overall_conf, "Pipeline")
        
        if "prediction_result" in final_state and final_state["prediction_result"]:
            prediction = final_state["prediction_result"]
            if "confidence" not in prediction or not isinstance(prediction["confidence"], dict):
                prediction["confidence"] = ConfidenceScore(score=0.5, level="moderate", explanation="Unknown", basis=[], suggestions=["Review"]).model_dump()
        else: prediction = None
        
        return sanitize_json({
            "job_id": final_state.get("job_id", ""),
            "prediction": prediction,
            "forecast": final_state.get("forecast_result"),
            "rca": final_state.get("rca_result"),
            "risk": final_state.get("risk_result"),
            "recommendation": final_state.get("recommendation_result"),
            "decision": final_state.get("decision_result"),
            "overall_confidence": final_state.get("overall_confidence", ConfidenceScore(score=0.0, level="uncertain", explanation="Failed", basis=[], suggestions=["Retry"]).model_dump()),
            "final_report": final_state.get("final_report", ""),
            "errors": final_state.get("errors", [])
        })
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.get("/pipeline-status")
async def pipeline_status():
    """
    Fetches the operational history and health scorecard of the decision pipeline execution.

    Returns:
        dict: Operational summary metrics.
    """
    return monitor.get_health_report()

@app.post("/explain")
async def explain(data: list[dict], target_column: str):
    """
    Computes global SHAP / feature importances for a customized XGBoost model trained on input records.

    Args:
        data (list[dict]): Tabular records to train and explain.
        target_column (str): Target column of prediction.

    Returns:
        dict: Full SHAP summary metrics and features plots data.
    """
    try:
        df = route_data(data)
        y = df[target_column]
        X = df.drop(columns=[target_column])
        X = X.select_dtypes(include=['number']).fillna(X.median())
        
        engine = PredictionEngine()
        task_type = engine.detect_task_type(y)
        
        from xgboost import XGBClassifier, XGBRegressor
        if task_type == "classification":
            from sklearn.preprocessing import LabelEncoder
            y = LabelEncoder().fit_transform(y)
            model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        else:
            model = XGBRegressor()
            
        model.fit(X, y)
        
        xai = XAILayer()
        result = xai.full_explanation(model, X, task_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format and column names"})

@app.get("/monitor")
async def get_monitor():
    """
    Retrieves system performance telemetry records and logs.

    Returns:
        dict: Monitor performance metadata.
    """
    return monitor.get_health_report()

@app.post("/monitor/drift")
async def monitor_drift(data: list[dict]):
    """
    Runs drift detection checking PSI metrics between baseline stats and incoming dataset records.

    Args:
        data (list[dict]): New incoming dataset records.

    Returns:
        dict: Summary of feature PSI values and detected drift flags.
    """
    try:
        df = pd.DataFrame(data)
        if not monitor.baseline_stats:
            monitor.set_baseline(df)
            return {"message": "Baseline set with current data."}
        return monitor.detect_drift(df)
    except Exception as e:
        raise HTTPException(status_code=422, detail={"error": "engine_failed", "message": str(e), "suggestion": "Check input data format"})
