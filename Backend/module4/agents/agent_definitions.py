from typing import Dict, Any
from schemas.models import ConfidenceScore
from engines.prediction_engine import PredictionEngine
from engines.forecasting_engine import ForecastingEngine
from engines.rca_agent import RCAAgent as RCAEngine
from engines.risk_engine import RiskEngine
from engines.recommendation_engine import RecommendationEngine
from engines.decision_engine import DecisionEngine

class BaseAgent:
    name: str = "BaseAgent"
    role: str = "Base Role"
    def run(self, state: dict) -> dict:
        raise NotImplementedError

class PredictionAgent(BaseAgent):
    name = "PredictionAgent"
    role = "Run AutoML pipeline and produce predictions with confidence"
    def run(self, state: dict) -> dict:
        try:
            engine = PredictionEngine()
            res = engine.train_and_predict(state["data"], state["target_column"])
            state["prediction_result"] = res
        except Exception as e:
            state["errors"].append(f"PredictionAgent error: {str(e)}")
            state["prediction_result"] = {
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class ForecastAgent(BaseAgent):
    name = "ForecastAgent"
    role = "Detect time-series columns and forecast future trends"
    def run(self, state: dict) -> dict:
        if not state.get("date_column"):
            return state
            
        try:
            engine = ForecastingEngine()
            res = engine.forecast(state["data"], state["date_column"], state["target_column"])
            state["forecast_result"] = res
        except Exception as e:
            state["errors"].append(f"ForecastAgent error: {str(e)}")
            state["forecast_result"] = {
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class RCAAgent(BaseAgent):
    name = "RCAAgent"
    role = "Identify root causes using SHAP analysis"
    def run(self, state: dict) -> dict:
        try:
            engine = RCAEngine()
            res = engine.analyse(state["data"], state["target_column"], state.get("problem", "analysis"))
            state["rca_result"] = res
        except Exception as e:
            state["errors"].append(f"RCAAgent error: {str(e)}")
            state["rca_result"] = {
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class RiskAgent(BaseAgent):
    name = "RiskAgent"
    role = "Detect anomalies and assess dataset risk level"
    def run(self, state: dict) -> dict:
        try:
            engine = RiskEngine()
            res = engine.detect(state["data"])
            state["risk_result"] = res
        except Exception as e:
            state["errors"].append(f"RiskAgent error: {str(e)}")
            state["risk_result"] = {
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class RecommendAgent(BaseAgent):
    name = "RecommendAgent"
    role = "Convert engine outputs into ranked actionable recommendations"
    def run(self, state: dict) -> dict:
        try:
            pred_conf = state.get("prediction_result", {}).get("confidence", {}).get("score", 0.0)
            risk_score = state.get("risk_result", {}).get("risk_score", 0.0)
            
            rca_res = state.get("rca_result", {})
            top_features = [f["feature"] for f in rca_res.get("top_features", [])]
            
            insights = ["Analysis running"]
            
            engine = RecommendationEngine()
            res = engine.recommend(insights, pred_conf, risk_score, top_features)
            state["recommendation_result"] = res
        except Exception as e:
            state["errors"].append(f"RecommendAgent error: {str(e)}")
            state["recommendation_result"] = {
                "recommendations": [],
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class DecisionAgent(BaseAgent):
    name = "DecisionAgent"
    role = "Synthesise all results into a strategic decision"
    def run(self, state: dict) -> dict:
        try:
            engine = DecisionEngine()
            res = engine.decide(
                state.get("prediction_result", {}),
                state.get("forecast_result"),
                state.get("rca_result", {}),
                state.get("risk_result", {}),
                state.get("recommendation_result", {})
            )
            state["decision_result"] = res
        except Exception as e:
            state["errors"].append(f"DecisionAgent error: {str(e)}")
            state["decision_result"] = {
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
                ).model_dump()
            }
        return state

class EvalAgent(BaseAgent):
    name = "EvalAgent"
    role = "Compute overall confidence and flag weak engines"
    def run(self, state: dict) -> dict:
        try:
            p_score = state.get("prediction_result", {}).get("confidence", {}).get("score", 0.0)
            f_score = state.get("forecast_result", {}).get("confidence", {}).get("score", 0.0) if state.get("forecast_result") else 0.0
            rca_score = state.get("rca_result", {}).get("confidence", {}).get("score", 0.0)
            risk_score = state.get("risk_result", {}).get("confidence", {}).get("score", 0.0)
            rec_score = state.get("recommendation_result", {}).get("confidence", {}).get("score", 0.0)
            dec_score = state.get("decision_result", {}).get("confidence", {}).get("score", 0.0)
            
            weighted_avg = (
                p_score * 0.25 +
                f_score * 0.15 +
                rca_score * 0.20 +
                risk_score * 0.15 +
                rec_score * 0.15 +
                dec_score * 0.10
            )
            
            scores_dict = {
                "prediction": p_score,
                "forecast": f_score if state.get("forecast_result") else float('inf'), # Ignore if didn't run
                "rca": rca_score,
                "risk": risk_score,
                "recommendation": rec_score,
                "decision": dec_score
            }
            
            limiting_factor = min(scores_dict, key=scores_dict.get)
            
            if weighted_avg >= 0.90: level = "very high"
            elif weighted_avg >= 0.75: level = "high"
            elif weighted_avg >= 0.55: level = "moderate"
            elif weighted_avg >= 0.40: level = "low"
            else: level = "uncertain"
            
            state["overall_confidence"] = ConfidenceScore(
                score=float(weighted_avg),
                level=level,
                explanation=f"Overall confidence is limited by {limiting_factor} engine.",
                basis=["Weighted average of component confidences"],
                suggestions=[f"Investigate {limiting_factor} to improve overall confidence."]
            ).model_dump()
            
        except Exception as e:
            state["errors"].append(f"EvalAgent error: {str(e)}")
            state["overall_confidence"] = ConfidenceScore(
                score=0.0, level="uncertain", explanation=f"Error: {str(e)}", basis=["Exception"], suggestions=["Check inputs"]
            ).model_dump()
        return state
