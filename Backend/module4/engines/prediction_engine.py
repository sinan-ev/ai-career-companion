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

    def train_and_predict(self, data: List[Dict[str, Any]], target_column: str = None) -> Dict[str, Any]:
        try:
            df = route_data(data)
            if df.empty:
                raise ValueError("The provided dataset is empty.")

            # 1. AI Domain and Target Discovery
            detected_domain = "General"
            if not target_column:
                # If no target, AI tries to find the most 'interesting' one
                cols = df.columns.tolist()
                # Priority: 'target', 'label', 'class', 'status', 'outcome', 'survived', 'churn', 'price'
                priority_keywords = ['target', 'label', 'class', 'status', 'outcome', 'survived', 'churn', 'price', 'species', 'wins']
                for kw in priority_keywords:
                    match = next((c for c in cols if kw in c.lower()), None)
                    if match:
                        target_column = match
                        break
                if not target_column: target_column = cols[-1] # Fallback to last column
            
            # Simple keyword-based domain detection for UI context
            col_str = " ".join(df.columns).lower()
            if any(k in col_str for k in ['survived', 'pclass', 'embarked']): detected_domain = "Maritime / Survival (Titanic)"
            elif any(k in col_str for k in ['sepal', 'petal', 'species']): detected_domain = "Biological / Species (Iris)"
            elif any(k in col_str for k in ['team', 'player', 'score', 'points', 'wins']): detected_domain = "Sports Analytics"
            elif any(k in col_str for k in ['attrition', 'salary', 'job', 'employee']): detected_domain = "Human Resources"
            elif any(k in col_str for k in ['patient', 'blood', 'heart', 'disease', 'medical']): detected_domain = "Healthcare"
            elif any(k in col_str for k in ['sales', 'revenue', 'customer', 'order']): detected_domain = "Sales & Retail"
            
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found.")
                
            y = df[target_column]
            self.task_type = self.detect_task_type(y)
            
            X = df.drop(columns=[target_column])
            
            # Drop non-numeric and fill nulls
            X = X.select_dtypes(include=['number'])
            X = X.fillna(X.median())
            self.feature_names = X.columns.tolist()
            
            if X.shape[1] == 0:
                raise ValueError("No numeric feature columns found after filtering. Please ensure your dataset has numeric columns.")
            
            self.task_type = self.detect_task_type(y)
            
            # Encode target if classification
            le = None
            if self.task_type == "classification":
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y = pd.Series(le.fit_transform(y), index=y.index)
            else:
                y = pd.to_numeric(y, errors='coerce').fillna(y.median())

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, 
                stratify=y if self.task_type == "classification" else None)

            # Dynamic CV Strategy
            cv_strategy = None
            if self.task_type == "classification":
                min_class_count = y_train.value_counts().min()
                if min_class_count >= 2:
                    cv_folds = max(2, min(5, int(min_class_count)))
                    from sklearn.model_selection import StratifiedKFold
                    cv_strategy = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            else:
                if len(y_train) >= 5:
                    cv_strategy = 5
                elif len(y_train) >= 2:
                    cv_strategy = len(y_train)

            best_model_name = None
            best_model = None
            best_score = 0.0 # Default to 0.0 instead of -inf
            
            if cv_strategy:
                if self.task_type == "classification":
                    from sklearn.linear_model import LogisticRegression
                    from sklearn.tree import DecisionTreeClassifier
                    models = {
                        "LGBMClassifier": LGBMClassifier(verbose=-1, n_estimators=100),
                        "RandomForestClassifier": RandomForestClassifier(random_state=42, n_estimators=100),
                        "XGBClassifier": XGBClassifier(eval_metric='logloss', verbosity=0, use_label_encoder=False),
                        "LogisticRegression": LogisticRegression(max_iter=500, random_state=42),
                        "DecisionTreeClassifier": DecisionTreeClassifier(random_state=42),
                    }
                else:
                    from sklearn.linear_model import Ridge
                    models = {
                        "LGBMRegressor": LGBMRegressor(verbose=-1, n_estimators=100),
                        "XGBRegressor": XGBRegressor(verbosity=0, n_estimators=100),
                        "RandomForestRegressor": RandomForestRegressor(random_state=42, n_estimators=100),
                        "Ridge": Ridge(),
                    }
                    
                cv_scoring = 'accuracy' if self.task_type == 'classification' else 'neg_mean_absolute_error'
                current_best_score = -float('inf')

                for name, m in models.items():
                    try:
                        scores = cross_val_score(
                            m, X_train, y_train, 
                            cv=cv_strategy, 
                            scoring=cv_scoring,
                            error_score=0
                        )
                        mean_score = scores.mean()
                        if mean_score > current_best_score:
                            current_best_score = mean_score
                            best_model_name = name
                            best_model = m
                    except Exception as model_err:
                        print(f"[PredictionEngine] Model '{name}' failed: {model_err}")
                        continue
                
                if best_model:
                    best_score = current_best_score

            # If ALL cross-val attempts failed or was skipped, fall back to direct fit
            if not best_model:
                print("[PredictionEngine] CV skipped or failed — using direct-fit fallback model")
                if self.task_type == 'classification':
                    from sklearn.linear_model import LogisticRegression
                    best_model = LogisticRegression(max_iter=1000, random_state=42)
                    best_model_name = "LogisticRegression (fallback)"
                else:
                    from sklearn.linear_model import Ridge
                    best_model = Ridge()
                    best_model_name = "Ridge (fallback)"
                
                best_model.fit(X_train, y_train)
                self.model = best_model
                best_score = 0.0 
            else:
                # Calibration for classification
                if self.task_type == "classification":
                    safe_cv = max(2, min(3, int(y_train.value_counts().min())))
                    if safe_cv >= 2:
                        try:
                            best_model = CalibratedClassifierCV(best_model, method='sigmoid', cv=safe_cv)
                            self.calibrated = True
                        except Exception as calib_err:
                            print(f"[PredictionEngine] Calibration skipped: {calib_err}")
                        
                best_model.fit(X_train, y_train)
                self.model = best_model

            
            y_pred = self.model.predict(X_test)

            if self.task_type == "classification":
                metrics = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "f1_weighted": f1_score(y_test, y_pred, average='weighted', zero_division=0)
                }
                # y_test is already encoded; inverse transform back to original labels
                actuals = le.inverse_transform(y_test.astype(int)) if le else y_test.values
                preds = le.inverse_transform(y_pred.astype(int)) if le else y_pred
                # Class distribution for the frontend chart
                class_dist = df[target_column].value_counts().to_dict()
                class_distribution = [{"label": str(k), "count": int(v)} for k, v in class_dist.items()]
            else:
                metrics = {
                    "mae": mean_absolute_error(y_test, y_pred),
                    "rmse": mean_squared_error(y_test, y_pred) ** 0.5,
                    "r2": r2_score(y_test, y_pred)
                }
                actuals = y_test.values
                preds = y_pred
                class_distribution = []
                
            predictions = []
            for i, (act, p) in enumerate(zip(actuals, preds)):
                predictions.append({
                    "index": i,
                    "actual": float(act) if pd.api.types.is_numeric_dtype(type(act)) else str(act),
                    "predicted": float(p) if pd.api.types.is_numeric_dtype(type(p)) else str(p)
                })
                
            confidence = self._compute_confidence(self.model, X_test, y_test, self.task_type)
            
            # --- LLM Business Summary ---
            from utils.llm_client import LLMClient
            import json
            
            try:
                llm = LLMClient()
                system_prompt = (
                    "You are a Business Intelligence AI. Summarize predictive modeling results for a non-technical executive. "
                    "Ignore technical jargon like 'XGBRegressor' or 'R-squared'. Focus purely on what we are predicting and "
                    "whether the AI feels confident in its ability to forecast this target outcome based on the dataset provided. "
                    "Keep it to 2-3 sentences max. Output MUST be valid JSON: {\"business_summary\": \"...\"}"
                )
                
                avg_predicted = "N/A (Classification)"
                avg_actual = "N/A (Classification)"
                if self.task_type != "classification" and predictions:
                    try:
                        avg_predicted = sum(float(p["predicted"]) for p in predictions) / len(predictions)
                        avg_actual = sum(float(p["actual"]) for p in predictions) / len(predictions)
                    except Exception:
                        pass
                
                class_info = ""
                if class_distribution:
                    dist_parts = [str(c['label']) + ': ' + str(c['count']) for c in class_distribution]
                    class_info = "\nClass Distribution: " + ", ".join(dist_parts)
                user_prompt = (
                    f"Dataset Domain: Auto-detected (could be HR, Healthcare, Sales, Finance, or any industry)\n"
                    f"Target Variable being predicted: {target_column}\n"
                    f"Prediction Task Type: {self.task_type}{class_info}\n"
                    f"AI Prediction Confidence: {confidence.level} ({confidence.score*100:.1f}%)\n"
                    f"Average Actual Value: {avg_actual} | Average Predicted Value: {avg_predicted}\n\n"
                    "Write an executive business summary (2-3 sentences) explaining:\n"
                    "1. What the AI is predicting and what that means for the business\n"
                    "2. Whether the business should trust and act on these predictions now\n"
                    "Keep the language completely non-technical and business-focused."
                )
                llm_res = llm.generate(system_prompt, user_prompt, require_json=True)
                llm_parsed = json.loads(llm_res)
                if "error" in llm_parsed:
                    business_summary = f"API Error: {llm_parsed['error']}"
                elif "business_summary" in llm_parsed:
                    business_summary = llm_parsed["business_summary"]
                else:
                    business_summary = f"AI returned unexpected JSON format: {llm_res}"
            except Exception as e:
                business_summary = f"The AI failed to generate a summary. Error: {str(e)} | Raw Output: {llm_res if 'llm_res' in locals() else 'None'}"

            return {
                "task_type": self.task_type,
                "domain": detected_domain,
                "model_used": best_model_name,
                "cv_score": float(best_score) if np.isfinite(best_score) else 0.0,
                "predictions": predictions,
                "metrics": metrics,
                "class_distribution": class_distribution,
                "business_summary": business_summary,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "task_type": "unknown",
                "model_used": "none",
                "cv_score": 0.0,
                "predictions": [],
                "metrics": {},
                "class_distribution": [],
                "business_summary": f"Prediction engine encountered an issue: {str(e)}",
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check input data format and target column."]
                ).model_dump()
            }
