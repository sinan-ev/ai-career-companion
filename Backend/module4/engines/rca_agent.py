# Dataset
#    ↓
# Train ML Model
#    ↓
# Feature Importance
#    ↓
# SHAP Analysis
#    ↓
# Causal Drivers
#    ↓
# Business Explanation
#    ↓
# Top Root Causes

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from lightgbm import LGBMRegressor, LGBMClassifier
import shap
from schemas.models import ConfidenceScore
from ingestion.data_router import route_data
from utils.llm_client import LLMClient
import json
import warnings

# Suppress specific library warnings for cleaner console output
warnings.filterwarnings("ignore", category=UserWarning, module="shap")
warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")

class RCAAgent:
    """
    Root Cause Analysis (RCA) explainability agent.

    Fits target-specific LightGBM trees and uses SHAP values across subset splits to calculate
    stable feature importance variance and discover primary causal drivers.
    """
    def _compute_confidence(self, shap_variance: float) -> ConfidenceScore:
        """
        Computes a reliability score for the root cause factors based on importance variance across splits.

        Args:
            shap_variance (float): The mean standard-deviation-to-importance ratio among top features.

        Returns:
            ConfidenceScore: Complete structural confidence details and suggestions.
        """
        try:
            score = max(0.3, 1.0 - (shap_variance * 10))
            score = float(np.clip(score, 0.0, 1.0))
        except Exception:
            score = 0.5
            
        if score >= 0.90:
            level = "very high"
            explanation = "Safe to act on this result automatically."
            suggestions = ["Review the identified top features."]
        elif score >= 0.75:
            level = "high"
            explanation = "Reliable result. Recommend quick human review."
            suggestions = ["Investigate top causal factors."]
        elif score >= 0.55:
            level = "moderate"
            explanation = "Reasonable result. Validate key assumptions."
            suggestions = ["Check feature importance stability over time."]
        elif score >= 0.40:
            level = "low"
            explanation = "Uncertain result. Expert review required."
            suggestions = ["High variance in SHAP analysis. Consult subject matter experts."]
        else:
            level = "uncertain"
            explanation = "Do not act. Collect more data first."
            suggestions = ["Unstable features. More data needed for reliable RCA."]

        basis = [f"SHAP Variance: {shap_variance:.4f}"]
        
        return ConfidenceScore(
            score=score,
            level=level,
            explanation=explanation,
            basis=basis,
            suggestions=suggestions
        )

    def analyse(self, data: List[Dict[str, Any]], target_column: str, problem: str) -> Dict[str, Any]:
        """
        Executes a multi-subset SHAP tree analysis to compute robust causal feature impacts.

        Fits model classifiers/regressors, runs SHAP explainers across train splits, sorts top features,
        synthesizes causal texts, and queries the LLM for Chief Strategy narrative translations.

        Args:
            data (List[Dict[str, Any]]): List of raw records to process.
            target_column (str): The prediction target column.
            problem (str): Text explanation of the analytical problem statement.

        Returns:
            Dict[str, Any]: RCA summary mapping top features list, causal chains, strategy narratives, and scores.
        """
        try:
            df = route_data(data)
            
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found.")
                
            y = df[target_column]
            X = df.drop(columns=[target_column])
            
            # Label encode categoricals
            for col in X.select_dtypes(include=['object', 'bool', 'category']).columns:
                X[col] = X[col].astype('category').cat.codes
                
            X = X.fillna(X.median())
            
            task_type = "classification" if y.nunique() <= 10 else "regression"
            
            if task_type == "classification":
                y = y.astype('category').cat.codes
                model = LGBMClassifier()
            else:
                model = LGBMRegressor()
                
            model.fit(X, y)
            
            subsets = [
                X.sample(frac=0.7, random_state=0),
                X.sample(frac=0.7, random_state=42),
                X
            ]
            
            shap_results = []
            
            for subset in subsets:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(subset)
                
                if isinstance(shap_values, list): # For multi-class
                    shap_values = shap_values[1] # Take positive class
                elif len(shap_values.shape) > 2:
                    # Take mean across classes
                    shap_values = np.abs(shap_values).mean(axis=-1)
                    
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
                if len(mean_abs_shap.shape) > 1:
                    mean_abs_shap = mean_abs_shap.mean(axis=1)
                shap_results.append(mean_abs_shap)
                
            shap_results_arr = np.array(shap_results)
            mean_importance = shap_results_arr.mean(axis=0)
            std_importance = shap_results_arr.std(axis=0)
            
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': mean_importance,
                'std': std_importance
            }).sort_values(by='importance', ascending=False)
            
            top_features = feature_importance.head(5).copy()
            
            # Robust variance calculation
            mean_importance_val = top_features['importance'].mean()
            if mean_importance_val == 0 or not np.isfinite(mean_importance_val):
                shap_variance = 0.0
            else:
                shap_variance = float(top_features['std'].mean() / (mean_importance_val + 1e-9))
            
            if not np.isfinite(shap_variance):
                shap_variance = 0.0
            
            top_features_list = []
            causal_chain = []
            
            for i, row in enumerate(top_features.itertuples()):
                # Improved heuristics for a business user
                importance_val = float(row.importance)
                if not np.isfinite(importance_val):
                    importance_val = 0.0
                if abs(importance_val) < 0.0001:
                    direction = "influences"
                else:
                    direction = "increases" if importance_val > 0 else "decreases"
                
                impact = "high" if i < 2 else ("medium" if i < 4 else "low")
                
                top_features_list.append({
                    "feature": row.feature,
                    "shap_value": importance_val,
                    "direction": direction,
                    "impact": impact
                })
                
                # Make text business-friendly:
                if task_type == "classification":
                    causal_chain.append(f"Higher values of {row.feature} {direction} the likelihood of {target_column}")
                else:
                    causal_chain.append(f"Higher values of {row.feature} {direction} the expected {target_column}")
                
            top_names = [f["feature"] for f in top_features_list[:3]]
            technical_explanation = f"The primary drivers of '{problem}' are {', '.join(top_names)}."
            
            # --- LLM Business Translation ---
            llm = LLMClient()
            system_prompt = (
                "You are a Chief Strategy Officer AI. "
                "Your job is to translate technical SHAP-based feature importance into actionable, "
                "business-understandable insights. "
                "Instead of just listing features, explain WHY these specific factors will cause the target metric (e.g. Sales) "
                "to increase or decrease in the upcoming forecast period. "
                "Provide a cohesive, forward-looking narrative that non-technical users can easily understand. "
                "Output MUST be in valid JSON format with a single key 'business_explanation' containing a string (2-4 sentences)."
            )
            user_prompt = (
                f"Business Objective / Problem: {problem}\n"
                f"Target Metric being Forecasted: {target_column}\n"
                f"Technical Causal Chain (SHAP derived):\n" + "\n".join(causal_chain) + "\n\n"
                "Please provide the strategic business explanation. Focus on WHY this happens and WHAT it means for upcoming trends."
            )
            
            try:
                llm_response = llm.generate(system_prompt, user_prompt, require_json=True)
                business_explanation = json.loads(llm_response).get("business_explanation", technical_explanation)
            except Exception:
                business_explanation = technical_explanation
            
            confidence = self._compute_confidence(shap_variance)
            
            return {
                "top_features": top_features_list,
                "causal_chain": causal_chain,
                "explanation": business_explanation,
                "technical_explanation": technical_explanation,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "top_features": [],
                "causal_chain": [],
                "explanation": f"Engine failed: {str(e)}",
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check input data format."]
                ).model_dump()
            }
