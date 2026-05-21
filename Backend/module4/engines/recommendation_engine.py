from typing import List, Dict, Any
from schemas.models import ConfidenceScore
from utils.llm_client import LLMClient
import json

class RecommendationEngine:
    """
    Strategic recommendation engine designed to translate raw data anomalies and predictions into ranked strategic actions.
    """
    RULES: List[Dict[str, Any]] = [
        {
            "id": 1, "condition_field": "risk_score", "condition_op": ">", "threshold": 70,
            "action": "Conduct Immediate Data Quality Audit", "rationale": "High risk score indicates severe data anomalies affecting insights.",
            "priority": "CRITICAL", "domain": "operations", "expected_impact": "High"
        },
        {
            "id": 2, "condition_field": "risk_score", "condition_op": ">", "threshold": 40,
            "action": "Review Outlier Transactions", "rationale": "Moderate risk score suggests some anomalous data points.",
            "priority": "HIGH", "domain": "operations", "expected_impact": "Medium"
        },
        {
            "id": 3, "condition_field": "prediction_confidence", "condition_op": "<", "threshold": 0.55,
            "action": "Gather More Historical Data Before Executing Strategy", "rationale": "The predictive trend has high uncertainty and needs more historical context to be reliable.",
            "priority": "HIGH", "domain": "business", "expected_impact": "High"
        },
        {
            "id": 4, "condition_field": "top_risk_features", "condition_op": "!=", "threshold": [],
            "action": "Optimize Business Operations around {top_feature}", "rationale": "This is the primary variable driving changes in your target outcomes.",
            "priority": "MEDIUM", "domain": "strategy", "expected_impact": "High"
        },
        {
            "id": 5, "condition_field": "general", "condition_op": "==", "threshold": "always",
            "action": "Review comprehensive AI strategy report", "rationale": "Align team on the generated insights before implementation.",
            "priority": "LOW", "domain": "general", "expected_impact": "Low"
        }
    ]

    def _evaluate_condition(self, value, op, threshold) -> bool:
        """
        Helper method to evaluate simple comparative logical operations.

        Args:
            value (any): Variable value.
            op (str): Operator string (">", "<", "==", "!=").
            threshold (any): Comparison boundary.

        Returns:
            bool: Result of the evaluation.
        """
        if op == ">": return value > threshold
        if op == "<": return value < threshold
        if op == "==": return value == threshold
        if op == "!=": return value != threshold
        return False

    def recommend(self, insights: List[str], prediction_confidence: float, risk_score: float, top_risk_features: List[str]) -> Dict[str, Any]:
        """
        Evaluates rule-based triggers and queries the strategic LLM model to compile actionable recommendations.

        Args:
            insights (List[str]): Extracted tabular insights.
            prediction_confidence (float): Calculated metric for prediction reliability.
            risk_score (float): Calculated anomalous risk score.
            top_risk_features (List[str]): Key drivers identified during Root Cause Analysis.

        Returns:
            Dict[str, Any]: Result mapping prioritized recommendations list and confidence scores.
        """
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

            # --- LLM Strategic Recommendations ---
            llm_recommendations = []
            try:
                llm = LLMClient()
                system_prompt = (
                    "You are a Chief Strategy Officer AI. Based on the insights from the analytics platform, "
                    "provide 3 highly strategic, actionable business recommendations that directly address how to improve the target outcome. "
                    "For example, if sales are influenced by a certain factor, explain what exact strategy the business should take to leverage or mitigate it to improve upcoming sales. "
                    "Make it easily understandable for non-technical users. "
                    "Output MUST be valid JSON in the format: {\"recommendations\": [{\"action\": \"Clear business strategy title\", \"rationale\": \"Why this strategy works and how it improves outcomes\", \"expected_impact\": \"High/Medium/Low\"}]}"
                )
                user_prompt = (
                    f"Platform Insights summary:\n"
                    f"- Prediction Confidence: {prediction_confidence}\n"
                    f"- Risk Score: {risk_score}\n"
                    f"- Top Influential Factors (Drivers): {', '.join(top_risk_features)}\n"
                    f"- Context Insights: {insights}\n\n"
                    "Generate 3 forward-looking business strategies to optimize the target metric based on these drivers."
                )
                llm_res = llm.generate(system_prompt, user_prompt, require_json=True)
                llm_parsed = json.loads(llm_res)
                
                for i, rec in enumerate(llm_parsed.get("recommendations", [])):
                    llm_recommendations.append({
                        "action": rec.get("action", f"Strategic Action {i+1}"),
                        "rationale": rec.get("rationale", "LLM-based rationale"),
                        "priority": "STRATEGIC",
                        "domain": "business",
                        "expected_impact": rec.get("expected_impact", "High"),
                        "confidence_score": overall_score
                    })
            except Exception as e:
                pass
                
            # Combine LLM and rule-based recommendations
            if len(llm_recommendations) > 0:
                # If we successfully got AI strategies, discard the generic rules to keep the UI clean
                final_recommendations = llm_recommendations
            else:
                final_recommendations = recommendations

            confidence = ConfidenceScore(
                score=overall_score,
                level=level,
                explanation="Score based on prediction confidence and inverse risk.",
                basis=["Prediction Confidence", "Risk Score"],
                suggestions=["Implement high priority recommendations to improve future confidence."]
            )
            
            return {
                "recommendations": final_recommendations,
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
