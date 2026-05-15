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
            
            # Build default strings (fallback)
            situation = f"Out of {total_records} records processed, we detected {anomaly_count} potential risks/anomalies ({anomaly_rate*100:.1f}% anomaly rate). The primary driving factor influencing this dataset is {top_rca_feature}."
            key_finding = f"Our AI predictive model reached a '{pred_conf_level}' confidence level. {top_rca_feature} was identified as the highest impact variable."
            strategic_decision = top_rec_action
            
            action_plan = [
                f"Step 1: {top_rec_action}",
                f"Step 2: Deep-dive into {top_rca_feature} as it's the primary driver",
                f"Step 3: Audit the {anomaly_count} flagged outlier records",
                "Step 4: Implement strategy and re-run analysis in 30 days"
            ]
            executive_summary = f"{situation} {key_finding} Recommended action: {strategic_decision}."

            # --- LLM Executive Briefing ---
            from utils.llm_client import LLMClient
            import json
            
            try:
                llm = LLMClient()
                system_prompt = (
                    "You are a CEO-level AI Advisor. Synthesize the analytics into a high-level executive strategic decision. "
                    "Make it business-focused, ignoring technical details like 'SHAP' or 'labelled samples'. "
                    "Output MUST be valid JSON: {\"situation\": \"...\", \"key_finding\": \"...\", \"strategic_decision\": \"...\", \"action_plan\": [\"...\", \"...\", \"...\", \"...\"], \"executive_summary\": \"...\"}"
                )
                user_prompt = (
                    f"RCA Feature: {top_rca_feature}\n"
                    f"Top Recommendation: {top_rec_action}\n"
                    f"Anomaly Rate: {anomaly_rate*100:.1f}%\n"
                    f"Prediction Confidence: {pred_conf_level}\n\n"
                    "Synthesize this into a cohesive 4-step action plan and strategic decision for the business."
                )
                llm_res = llm.generate(system_prompt, user_prompt, require_json=True)
                llm_parsed = json.loads(llm_res)
                
                situation = llm_parsed.get("situation", situation)
                key_finding = llm_parsed.get("key_finding", key_finding)
                strategic_decision = llm_parsed.get("strategic_decision", strategic_decision)
                action_plan = llm_parsed.get("action_plan", action_plan)
                executive_summary = llm_parsed.get("executive_summary", executive_summary)
            except Exception:
                pass
            
            # Confidence
            scores = [
                prediction.get("confidence", {}).get("score", 0.5),
                rca.get("confidence", {}).get("score", 0.5),
                risk.get("confidence", {}).get("score", 0.5),
                recommendation.get("confidence", {}).get("score", 0.5)
            ]
            
            import numpy as np
            scores = [float(s) for s in scores if np.isfinite(s)]
            if not scores:
                scores = [0.5]
            
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
