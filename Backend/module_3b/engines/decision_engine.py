from typing import Dict, Any, Optional
from schemas.models import ConfidenceScore

class DecisionEngine:
    def decide(self, prediction: Dict[str, Any], forecast: Optional[Dict[str, Any]], rca: Dict[str, Any], risk: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract key values
            anomaly_count = risk.get("anomaly_count", 0)
            anomaly_rate = risk.get("anomaly_rate", 0.0)
            total_records = risk.get("total_records", 0)
            
            top_rca_feature = "Unknown"
            shap_val = 0.0
            top_features = rca.get("top_features", [])
            if top_features:
                top_rca_feature = top_features[0].get("feature", "Unknown")
                shap_val = top_features[0].get("shap_value", 0.0)
                
            task_type = prediction.get("task_type", "unknown task")
            pred_conf_level = prediction.get("confidence", {}).get("level", "uncertain")
            
            recs = recommendation.get("recommendations", [])
            top_rec_action = recs[0].get("action", "Review full report") if recs else "Review full report"
            
            # Build strings
            situation = f"Analysis of {total_records} records identified {anomaly_count} anomalies ({anomaly_rate*100:.1f}% anomaly rate). Primary driver: {top_rca_feature}."
            key_finding = f"The model predicts {task_type} outcomes with {pred_conf_level} confidence. Top risk factor: {top_rca_feature} (SHAP: {shap_val:.4f})."
            strategic_decision = top_rec_action
            
            action_plan = [
                f"Step 1: {top_rec_action}",
                f"Step 2: Investigate {top_rca_feature} — primary root cause",
                f"Step 3: Review {anomaly_count} flagged anomalous records",
                "Step 4: Re-evaluate pipeline after implementing Step 1"
            ]
            
            executive_summary = f"{situation} {key_finding} Recommended action: {strategic_decision}."
            
            # Confidence
            scores = [
                prediction.get("confidence", {}).get("score", 0.5),
                rca.get("confidence", {}).get("score", 0.5),
                risk.get("confidence", {}).get("score", 0.5),
                recommendation.get("confidence", {}).get("score", 0.5)
            ]
            
            weakest_score = min(scores)
            
            if weakest_score < 0.50:
                executive_summary += " ⚠ Low confidence — human review required."
                
            if weakest_score >= 0.90: level = "very high"
            elif weakest_score >= 0.75: level = "high"
            elif weakest_score >= 0.55: level = "moderate"
            elif weakest_score >= 0.40: level = "low"
            else: level = "uncertain"
            
            limiting_factor = "Unknown"
            if weakest_score == scores[0]: limiting_factor = "Prediction"
            elif weakest_score == scores[1]: limiting_factor = "RCA"
            elif weakest_score == scores[2]: limiting_factor = "Risk"
            elif weakest_score == scores[3]: limiting_factor = "Recommendation"

            confidence = ConfidenceScore(
                score=float(weakest_score),
                level=level,
                explanation=f"Confidence is limited by {limiting_factor} engine.",
                basis=["Prediction Score", "RCA Score", "Risk Score", "Recommendation Score"],
                suggestions=[f"Improve the {limiting_factor} process to boost overall confidence."]
            )
            
            return {
                "situation": situation,
                "key_finding": key_finding,
                "strategic_decision": strategic_decision,
                "action_plan": action_plan,
                "executive_summary": executive_summary,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "situation": "Engine failed",
                "key_finding": str(e),
                "strategic_decision": "Review errors",
                "action_plan": ["Fix engine failure"],
                "executive_summary": f"Failed: {str(e)}",
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check inputs and logs."]
                ).model_dump()
            }
