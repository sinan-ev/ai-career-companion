from typing import List, Dict, Any
from schemas.models import ConfidenceScore

class RecommendationEngine:
    RULES: List[Dict[str, Any]] = [
        {
            "id": 1, "condition_field": "risk_score", "condition_op": ">", "threshold": 70,
            "action": "Immediate anomaly audit required", "rationale": "High risk score indicates severe data issues.",
            "priority": "CRITICAL", "domain": "operations", "expected_impact": "High"
        },
        {
            "id": 2, "condition_field": "risk_score", "condition_op": ">", "threshold": 40,
            "action": "Investigate flagged records", "rationale": "Moderate risk score suggests some data anomalies.",
            "priority": "HIGH", "domain": "data quality", "expected_impact": "Medium"
        },
        {
            "id": 3, "condition_field": "prediction_confidence", "condition_op": "<", "threshold": 0.55,
            "action": "Collect 200+ more labelled samples", "rationale": "Low prediction confidence requires more training data.",
            "priority": "HIGH", "domain": "ml", "expected_impact": "High"
        },
        {
            "id": 4, "condition_field": "prediction_confidence", "condition_op": "<", "threshold": 0.40,
            "action": "Do not use predictions — retrain first", "rationale": "Prediction confidence is too low for safe use.",
            "priority": "CRITICAL", "domain": "ml", "expected_impact": "High"
        },
        {
            "id": 5, "condition_field": "anomaly_rate", "condition_op": ">", "threshold": 0.10,
            "action": "Review data collection pipeline", "rationale": "Anomaly rate exceeds 10%, indicating pipeline issues.",
            "priority": "HIGH", "domain": "data quality", "expected_impact": "High"
        },
        {
            "id": 6, "condition_field": "anomaly_rate", "condition_op": ">", "threshold": 0.20,
            "action": "Halt automated decisions pending review", "rationale": "Severe anomaly rate ( > 20%) requires manual intervention.",
            "priority": "CRITICAL", "domain": "operations", "expected_impact": "High"
        },
        {
            "id": 7, "condition_field": "risk_score", "condition_op": "<", "threshold": 10,
            "action": "Data quality is healthy — proceed", "rationale": "Risk score is low, data is safe to use.",
            "priority": "LOW", "domain": "operations", "expected_impact": "Low"
        },
        {
            "id": 8, "condition_field": "prediction_confidence", "condition_op": ">", "threshold": 0.85,
            "action": "Confidence is high — safe to automate", "rationale": "High prediction confidence allows automation.",
            "priority": "LOW", "domain": "ml", "expected_impact": "High"
        },
        {
            "id": 9, "condition_field": "top_risk_features", "condition_op": "!=", "threshold": [],
            "action": "Deep-dive feature [{top_feature}] — top risk driver", "rationale": "Key feature identified as primary risk driver.",
            "priority": "MEDIUM", "domain": "analysis", "expected_impact": "Medium"
        },
        {
            "id": 10, "condition_field": "general", "condition_op": "==", "threshold": "always",
            "action": "Review executive report for full insights", "rationale": "General review recommended for all analyses.",
            "priority": "LOW", "domain": "general", "expected_impact": "Low"
        }
    ]

    def _evaluate_condition(self, value, op, threshold) -> bool:
        if op == ">": return value > threshold
        if op == "<": return value < threshold
        if op == "==": return value == threshold
        if op == "!=": return value != threshold
        return False

    def recommend(self, insights: List[str], prediction_confidence: float, risk_score: float, top_risk_features: List[str]) -> Dict[str, Any]:
        try:
            anomaly_rate = risk_score / 100.0
            
            inputs = {
                "risk_score": risk_score,
                "prediction_confidence": prediction_confidence,
                "anomaly_rate": anomaly_rate,
                "top_risk_features": top_risk_features,
                "general": "always"
            }
            
            triggered_rules = []
            for rule in self.RULES:
                field = rule["condition_field"]
                op = rule["condition_op"]
                threshold = rule["threshold"]
                
                val = inputs.get(field)
                
                if field == "top_risk_features" and len(top_risk_features) > 0:
                    action = rule["action"].replace("{top_feature}", top_risk_features[0])
                    triggered_rules.append({**rule, "action": action})
                elif field != "top_risk_features" and self._evaluate_condition(val, op, threshold):
                    triggered_rules.append(rule)
                    
            if len(triggered_rules) < 2:
                triggered_rules.append(self.RULES[9]) # general rule
                
            priority_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            triggered_rules.sort(key=lambda x: priority_map.get(x["priority"], 0), reverse=True)
            
            recommendations = []
            for rule in triggered_rules:
                conf_score = (prediction_confidence + (1 - risk_score/100.0)) / 2
                recommendations.append({
                    "action": rule["action"],
                    "rationale": rule["rationale"],
                    "priority": rule["priority"],
                    "domain": rule["domain"],
                    "expected_impact": rule["expected_impact"],
                    "confidence_score": float(conf_score)
                })
                
            overall_score = (prediction_confidence * 0.6) + ((1 - risk_score/100.0) * 0.4)
            overall_score = max(0.0, min(1.0, float(overall_score)))
            
            if overall_score >= 0.90: level = "very high"
            elif overall_score >= 0.75: level = "high"
            elif overall_score >= 0.55: level = "moderate"
            elif overall_score >= 0.40: level = "low"
            else: level = "uncertain"

            confidence = ConfidenceScore(
                score=overall_score,
                level=level,
                explanation="Score based on prediction confidence and inverse risk.",
                basis=["Prediction Confidence", "Risk Score"],
                suggestions=["Implement high priority recommendations to improve future confidence."]
            )
            
            return {
                "recommendations": recommendations,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "recommendations": [],
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check input values."]
                ).model_dump()
            }
