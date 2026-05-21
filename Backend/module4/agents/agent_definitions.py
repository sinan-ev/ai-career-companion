from typing import Dict, Any
from schemas.models import ConfidenceScore
from engines.prediction_engine import PredictionEngine
from engines.forecasting_engine import ForecastingEngine
from engines.rca_agent import RCAAgent as RCAEngine
from engines.risk_engine import RiskEngine
from engines.recommendation_engine import RecommendationEngine
from engines.decision_engine import DecisionEngine

class BaseAgent:
    """
    Abstract base class representing an autonomous agent in the Module 4 task flow.
    """
    name: str = "BaseAgent"
    role: str = "Base Role"
    def run(self, state: dict) -> dict:
        """
        Executes the agent's logic on the shared workflow state.

        Args:
            state (dict): The shared workspace state mapping of values.

        Returns:
            dict: The updated workflow state dictionary.

        Raises:
            NotImplementedError: If not implemented in the subclass.
        """
        raise NotImplementedError

class PredictionAgent(BaseAgent):
    """
    AutoML prediction agent responsible for training models and generating forecasts/predictions.
    """
    name = "PredictionAgent"
    role = "Run AutoML pipeline and produce predictions with confidence"
    def run(self, state: dict) -> dict:
        """
        Runs prediction engine over active data state.

        Args:
            state (dict): Shared dictionary containing 'data' and 'target_column'.

        Returns:
            dict: State with populated 'prediction_result'.
        """
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
    """
    Time series forecasting agent that identifies trends over time-series coordinates.
    """
    name = "ForecastAgent"
    role = "Detect time-series columns and forecast future trends"
    def run(self, state: dict) -> dict:
        """
        Runs forecasting engine over historical time series data.

        Args:
            state (dict): Shared dictionary containing 'data', 'date_column', and 'target_column'.

        Returns:
            dict: State with populated 'forecast_result'.
        """
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
    """
    Root Cause Analysis (SHAP-based explainability) agent.
    """
    name = "RCAAgent"
    role = "Identify root causes using SHAP analysis"
    def run(self, state: dict) -> dict:
        """
        Runs RCA (SHAP) explainability analysis to find most predictive features.

        Args:
            state (dict): Shared dictionary containing 'data', 'target_column', and 'problem'.

        Returns:
            dict: State with populated 'rca_result'.
        """
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
    """
    Anomaly detection and overall dataset risk assessment agent.
    """
    name = "RiskAgent"
    role = "Detect anomalies and assess dataset risk level"
    def run(self, state: dict) -> dict:
        """
        Detects anomalies and generates global risk assessments on inputs.

        Args:
            state (dict): Shared dictionary containing 'data'.

        Returns:
            dict: State with populated 'risk_result'.
        """
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
    """
    Actionable recommendations generator agent.
    """
    name = "RecommendAgent"
    role = "Convert engine outputs into ranked actionable recommendations"
    def run(self, state: dict) -> dict:
        """
        Translates multi-engine findings into prioritized actionable recommendations.

        Args:
            state (dict): Shared dictionary carrying prediction and risk score results.

        Returns:
            dict: State with populated 'recommendation_result'.
        """
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
    """
    Decision synthesising agent that resolves multi-engine predictions into an executive decree.
    """
    name = "DecisionAgent"
    role = "Synthesise all results into a strategic decision"
    def run(self, state: dict) -> dict:
        """
        Executes decision synthesis across prediction, forecast, RCA, risk, and recommendations.

        Args:
            state (dict): Shared workflow dictionary state.

        Returns:
            dict: State with populated 'decision_result'.
        """
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
    """
    Global system evaluator agent checking overall reliability.
    """
    name = "EvalAgent"
    role = "Compute overall confidence and flag weak engines"
    def run(self, state: dict) -> dict:
        """
        Scores overall pipeline confidence as a weighted average and determines bottleneck limits.

        Args:
            state (dict): Shared workflow dictionary state.

        Returns:
            dict: State with populated 'overall_confidence'.
        """
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
