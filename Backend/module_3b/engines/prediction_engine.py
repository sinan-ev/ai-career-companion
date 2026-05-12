import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, f1_score, classification_report, mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from schemas.models import ConfidenceScore
from ingestion.data_router import route_data

class PredictionEngine:
    def __init__(self):
        self.model = None
        self.task_type = None
        self.feature_names = []
        self.calibrated = False

    def detect_task_type(self, y: pd.Series) -> str:
        """Detect classification vs regression."""
        if y.dtype == 'object' or y.dtype == 'bool' or pd.api.types.is_categorical_dtype(y):
            return "classification"
        if y.nunique() <= 10 and (y.nunique() / len(y)) < 0.05:
            return "classification"
        return "regression"

    def _compute_confidence(self, model, X_test, y_test, task_type) -> ConfidenceScore:
        try:
            if task_type == "classification":
                probas = model.predict_proba(X_test)
                mean_max_proba = float(pd.DataFrame(probas).max(axis=1).mean())
                score = mean_max_proba
            else:
                y_pred = model.predict(X_test)
                residuals = abs(y_pred - y_test)
                normalised_error = residuals.mean() / (y_test.std() + 1e-9)
                score = max(0.0, 1.0 - normalised_error)
        except Exception:
            score = 0.5
            
        if score >= 0.90:
            level = "very high"
            explanation = "Safe to act on this result automatically."
            suggestions = ["Monitor performance over time."]
        elif score >= 0.75:
            level = "high"
            explanation = "Reliable result. Recommend quick human review."
            suggestions = ["Check predictions on edge cases."]
        elif score >= 0.55:
            level = "moderate"
            explanation = "Reasonable result. Validate key assumptions."
            suggestions = ["Consider gathering more features.", "Check data balance."]
        elif score >= 0.40:
            level = "low"
            explanation = "Uncertain result. Expert review required."
            suggestions = ["Model needs tuning.", "More training data required."]
        else:
            level = "uncertain"
            explanation = "Do not act. Collect more data first."
            suggestions = ["Significant data quality issues.", "Completely retrain with new data."]

        basis = [f"Task Type: {task_type}", f"Dataset Size: {len(y_test) * 5}"] # approx total size
        
        return ConfidenceScore(
            score=float(score),
            level=level,
            explanation=explanation,
            basis=basis,
            suggestions=suggestions
        )

    def train_and_predict(self, data: List[Dict[str, Any]], target_column: str) -> Dict[str, Any]:
        try:
            df = route_data(data)
            
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found.")
                
            y = df[target_column]
            X = df.drop(columns=[target_column])
            
            # Drop non-numeric and fill nulls
            X = X.select_dtypes(include=['number'])
            X = X.fillna(X.median())
            self.feature_names = X.columns.tolist()
            
            self.task_type = self.detect_task_type(y)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            if self.task_type == "classification":
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y_train = le.fit_transform(y_train)
                y_test = le.transform(y_test)
                
                models = {
                    "XGBClassifier": XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
                    "LGBMClassifier": LGBMClassifier(),
                    "RandomForestClassifier": RandomForestClassifier(random_state=42)
                }
                scoring = 'accuracy'
            else:
                models = {
                    "XGBRegressor": XGBRegressor(),
                    "LGBMRegressor": LGBMRegressor(),
                    "RandomForestRegressor": RandomForestRegressor(random_state=42)
                }
                scoring = 'neg_mean_absolute_error'
                
            best_model_name = None
            best_model = None
            best_score = -float('inf')
            
            for name, m in models.items():
                try:
                    scores = cross_val_score(m, X_train, y_train, cv=5, scoring=scoring)
                    mean_score = scores.mean()
                    if mean_score > best_score:
                        best_score = mean_score
                        best_model_name = name
                        best_model = m
                except Exception:
                    continue
                    
            if not best_model:
                raise ValueError("All models failed during cross-validation.")
                
            if self.task_type == "classification":
                best_model = CalibratedClassifierCV(best_model, method='isotonic', cv=5)
                self.calibrated = True
                
            best_model.fit(X_train, y_train)
            self.model = best_model
            
            y_pred = self.model.predict(X_test)
            
            if self.task_type == "classification":
                metrics = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "f1_weighted": f1_score(y_test, y_pred, average='weighted')
                }
                actuals = le.inverse_transform(y_test)
                preds = le.inverse_transform(y_pred)
            else:
                metrics = {
                    "mae": mean_absolute_error(y_test, y_pred),
                    "rmse": mean_squared_error(y_test, y_pred) ** 0.5,
                    "r2": r2_score(y_test, y_pred)
                }
                actuals = y_test.values
                preds = y_pred
                
            predictions = []
            for i, (act, p) in enumerate(zip(actuals, preds)):
                predictions.append({
                    "index": i,
                    "actual": float(act) if pd.api.types.is_numeric_dtype(type(act)) else str(act),
                    "predicted": float(p) if pd.api.types.is_numeric_dtype(type(p)) else str(p)
                })
                
            confidence = self._compute_confidence(self.model, X_test, y_test, self.task_type)
            
            return {
                "task_type": self.task_type,
                "model_used": best_model_name,
                "cv_score": float(best_score),
                "predictions": predictions,
                "metrics": metrics,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "task_type": "unknown",
                "model_used": "none",
                "cv_score": 0.0,
                "predictions": [],
                "metrics": {},
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check input data format and target column."]
                ).model_dump()
            }
