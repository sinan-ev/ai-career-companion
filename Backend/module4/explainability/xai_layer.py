import pandas as pd
import numpy as np
import shap
import lime
import lime.lime_tabular
from typing import Dict, Any, List
from schemas.models import ConfidenceScore

class XAILayer:
    """
    Explainability layer aggregating SHAP and LIME interpretability techniques
    alongside native model feature importances to generate global and local prediction explanations.
    """
    def explain_with_shap(self, model, X: pd.DataFrame, task_type: str) -> Dict[str, Any]:
        """
        Computes global SHAP feature importances across all provided samples.

        Args:
            model: Trained tree-based model compatible with shap.TreeExplainer.
            X (pd.DataFrame): Feature matrix to explain.
            task_type (str): Either "classification" or "regression".

        Returns:
            Dict[str, Any]: Dictionary mapping global importance values, top feature rankings, and summary text.
        """
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            
            if isinstance(shap_values, list): # Multi-class
                shap_values = shap_values[1]
                
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': mean_abs_shap
            }).sort_values(by='importance', ascending=False)
            
            global_importance = dict(zip(feature_importance['feature'], feature_importance['importance']))
            top_features = feature_importance.head(10).to_dict('records')
            
            top_name = top_features[0]['feature'] if top_features else "unknown"
            summary = f"Feature '{top_name}' has the highest influence on predictions."
            
            return {
                "global_importance": global_importance,
                "top_features": top_features,
                "summary": summary
            }
        except Exception as e:
            return {"error": str(e), "summary": "SHAP explanation failed."}

    def explain_with_lime(self, model, X: pd.DataFrame, row_index: int, task_type: str) -> Dict[str, Any]:
        try:
            mode = 'classification' if task_type == 'classification' else 'regression'
            explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data=X.values,
                feature_names=X.columns.tolist(),
                mode=mode,
                random_state=42
            )
            
            predict_fn = model.predict_proba if mode == 'classification' else model.predict
            
            exp = explainer.explain_instance(X.iloc[row_index].values, predict_fn, num_features=5)
            
            explanation = exp.as_list()
            predicted_value = float(predict_fn(X.iloc[row_index:row_index+1].values)[0])
            
            top_factors = [f[0] for f in explanation[:2]]
            summary = f"The most significant local factors for this prediction are: {', '.join(top_factors)}."
            
            return {
                "explanation": explanation,
                "predicted_value": predicted_value,
                "summary": summary
            }
        except Exception as e:
            return {"error": str(e), "summary": "LIME explanation failed."}

    def feature_importance_report(self, model, feature_names: List[str]) -> Dict[str, float]:
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                fi_dict = dict(zip(feature_names, importances))
                return dict(sorted(fi_dict.items(), key=lambda item: item[1], reverse=True))
            return {}
        except Exception:
            return {}

    def full_explanation(self, model, X: pd.DataFrame, task_type: str) -> Dict[str, Any]:
        try:
            shap_res = self.explain_with_shap(model, X, task_type)
            native_fi = self.feature_importance_report(model, X.columns.tolist())
            
            # compute agreement score
            agreement_score = 0.5
            if shap_res and "global_importance" in shap_res and native_fi:
                shap_top = list(shap_res["global_importance"].keys())[:5]
                native_top = list(native_fi.keys())[:5]
                intersection = set(shap_top).intersection(set(native_top))
                agreement_score = len(intersection) / 5.0
                
            if agreement_score >= 0.8: level = "high"
            elif agreement_score >= 0.4: level = "moderate"
            else: level = "low"
            
            confidence = ConfidenceScore(
                score=float(agreement_score),
                level=level,
                explanation="Confidence based on agreement between SHAP and native feature importances.",
                basis=["SHAP vs Native Importance correlation"],
                suggestions=["If low, check model stability and feature correlations."]
            )
            
            return {
                "shap_explanation": shap_res,
                "native_feature_importance": native_fi,
                "agreement_score": float(agreement_score),
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "error": str(e),
                "confidence": ConfidenceScore(
                    score=0.0, level="uncertain", explanation="Failed", basis=[], suggestions=["Fix code"]
                ).model_dump()
            }
