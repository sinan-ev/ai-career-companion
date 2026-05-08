import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

class ModelMonitor:
    def __init__(self):
        self.run_history: List[Dict[str, Any]] = []
        self.baseline_stats: Dict[str, Any] = {}

    def log_run(self, job_id: str, metrics: Dict[str, Any], confidence: float, engine: str):
        record = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "engine": engine,
            "metrics": metrics,
            "confidence": confidence,
            "status": "success" if confidence > 0.0 else "failed"
        }
        self.run_history.append(record)

    def set_baseline(self, data: pd.DataFrame):
        df_num = data.select_dtypes(include=['number'])
        stats = {}
        for col in df_num.columns:
            stats[col] = {
                "mean": float(df_num[col].mean()),
                "std": float(df_num[col].std()),
                "min": float(df_num[col].min()),
                "max": float(df_num[col].max()),
                "dtype": str(df_num[col].dtype)
            }
        self.baseline_stats = stats

    def detect_drift(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        if not self.baseline_stats:
            return {"error": "No baseline set. Call set_baseline first."}
            
        df_num = new_data.select_dtypes(include=['number'])
        drifted_columns = []
        drift_scores = {}
        
        for col in df_num.columns:
            if col in self.baseline_stats:
                base_mean = self.baseline_stats[col]["mean"]
                base_std = self.baseline_stats[col]["std"]
                
                new_mean = float(df_num[col].mean())
                
                drift_score = abs(new_mean - base_mean) / (base_std + 1e-9)
                drift_scores[col] = drift_score
                
                if drift_score > 2.0:
                    drifted_columns.append(col)
                    
        overall_drift = len(drifted_columns) > 0
        recommendation = "Data distribution has drifted significantly. Consider retraining." if overall_drift else "No significant drift detected."
        
        return {
            "drifted_columns": drifted_columns,
            "drift_scores": drift_scores,
            "overall_drift": overall_drift,
            "recommendation": recommendation
        }

    def get_health_report(self) -> Dict[str, Any]:
        total_runs = len(self.run_history)
        last_run_time = self.run_history[-1]["timestamp"] if total_runs > 0 else None
        
        recent_runs = self.run_history[-10:]
        recent_confidences = [r["confidence"] for r in recent_runs if "confidence" in r]
        avg_confidence_last_10 = sum(recent_confidences) / len(recent_confidences) if recent_confidences else 0.0
        
        confidence_trend = "stable"
        if len(recent_confidences) >= 5:
            first_half = sum(recent_confidences[:len(recent_confidences)//2]) / (len(recent_confidences)//2)
            second_half = sum(recent_confidences[len(recent_confidences)//2:]) / (len(recent_confidences) - len(recent_confidences)//2)
            if second_half > first_half + 0.05: confidence_trend = "improving"
            elif second_half < first_half - 0.05: confidence_trend = "declining"
            
        engines_run = list(set([r["engine"] for r in self.run_history]))
        recent_errors = [r for r in recent_runs if r["status"] == "failed"]
        
        return {
            "total_runs": total_runs,
            "last_run_time": last_run_time,
            "avg_confidence_last_10": avg_confidence_last_10,
            "confidence_trend": confidence_trend,
            "engines_run": engines_run,
            "recent_errors": recent_errors
        }
