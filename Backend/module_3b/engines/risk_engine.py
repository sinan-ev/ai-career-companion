import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
from schemas.models import ConfidenceScore
from ingestion.data_router import route_data

class RiskEngine:
    def _compute_confidence(self, flags_a: np.ndarray, flags_b: np.ndarray, flags_c: np.ndarray) -> ConfidenceScore:
        try:
            total_rows = len(flags_a)
            if total_rows == 0:
                return ConfidenceScore(score=0.5, level="moderate", explanation="Empty dataset", basis=[], suggestions=["Add data"])
                
            agreements = (flags_a == flags_b) & (flags_b == flags_c)
            agreement_rate = np.sum(agreements) / total_rows
            
            score = 0.50 + (agreement_rate * 0.50)
            score = float(np.clip(score, 0.0, 1.0))
        except Exception:
            score = 0.5
            
        if score >= 0.90:
            level = "very high"
            explanation = "Safe to act on this result automatically."
            suggestions = ["Monitor anomaly sources."]
        elif score >= 0.75:
            level = "high"
            explanation = "Reliable result. Recommend quick human review."
            suggestions = ["Investigate flagged anomalies."]
        elif score >= 0.55:
            level = "moderate"
            explanation = "Reasonable result. Validate key assumptions."
            suggestions = ["Examine features contributing to low agreement."]
        elif score >= 0.40:
            level = "low"
            explanation = "Uncertain result. Expert review required."
            suggestions = ["Detectors strongly disagree. Expert review required."]
        else:
            level = "uncertain"
            explanation = "Do not act. Collect more data first."
            suggestions = ["Data quality is severely compromised."]

        basis = [f"Detector Agreement Rate: {agreement_rate:.2%}"]
        
        return ConfidenceScore(
            score=score,
            level=level,
            explanation=explanation,
            basis=basis,
            suggestions=suggestions
        )

    def detect(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            df = route_data(data)
            df_num = df.select_dtypes(include=['number']).copy()
            df_num = df_num.fillna(df_num.median())
            
            if df_num.empty:
                raise ValueError("No numeric columns found for anomaly detection.")
                
            X = df_num.values
            
            # Detector A
            clf = IsolationForest(contamination=0.05, random_state=42)
            flags_a = clf.fit_predict(X) == -1
            
            # Detector B
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with np.errstate(invalid='ignore'):
                    z_scores = np.abs(stats.zscore(X, nan_policy='omit'))
            flags_b = np.any(z_scores > 3.0, axis=1)
            
            # Detector C
            Q1 = df_num.quantile(0.25)
            Q3 = df_num.quantile(0.75)
            IQR = Q3 - Q1
            flags_c = ((df_num < (Q1 - 1.5 * IQR)) | (df_num > (Q3 + 1.5 * IQR))).any(axis=1).values
            
            votes = flags_a.astype(int) + flags_b.astype(int) + flags_c.astype(int)
            anomaly = votes >= 2
            
            total_records = len(df)
            anomaly_count = int(np.sum(anomaly))
            anomaly_rate = float(anomaly_count / total_records)
            risk_score = float(anomaly_rate * 100)
            
            if risk_score > 70:
                alert = "CRITICAL: High anomaly rate — immediate review needed"
            elif risk_score > 40:
                alert = "WARNING: Moderate anomalies — investigate flagged rows"
            elif risk_score > 10:
                alert = "INFO: Minor anomalies detected"
            else:
                alert = "CLEAR: No significant anomalies detected"
                
            anomalous_indices = np.where(anomaly)[0].tolist()
            
            confidence = self._compute_confidence(flags_a, flags_b, flags_c)
            
            return {
                "total_records": total_records,
                "anomaly_count": anomaly_count,
                "anomaly_rate": anomaly_rate,
                "risk_score": risk_score,
                "alerts": [alert],
                "anomalous_indices": anomalous_indices,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "total_records": len(data) if data else 0,
                "anomaly_count": 0,
                "anomaly_rate": 0.0,
                "risk_score": 0.0,
                "alerts": [f"Engine failed: {str(e)}"],
                "anomalous_indices": [],
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check input data format."]
                ).model_dump()
            }
