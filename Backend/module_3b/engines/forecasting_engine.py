import pandas as pd
import numpy as np
from typing import List, Dict, Any
from prophet import Prophet
import pmdarima as pm
from schemas.models import ConfidenceScore
from ingestion.data_router import route_data

class ForecastingEngine:
    def _compute_confidence(self, prophet_mae: float, arima_mae: float, interval_widths: List[float], mean_forecast_value: float) -> ConfidenceScore:
        try:
            max_mae = max(prophet_mae, arima_mae)
            model_agreement = 1 - abs(prophet_mae - arima_mae) / (max_mae + 1e-9)
            interval_penalty = np.mean(interval_widths) / (mean_forecast_value + 1e-9)
            
            score = (model_agreement * 0.6) + (max(0, 1 - interval_penalty) * 0.4)
            score = float(np.clip(score, 0.0, 1.0))
            
            if prophet_mae < mean_forecast_value * 0.1 and arima_mae < mean_forecast_value * 0.1 and model_agreement > 0.85:
                score = min(1.0, score + 0.05)
        except Exception:
            score = 0.5
            
        if score >= 0.90:
            level = "very high"
            explanation = "Safe to act on this result automatically."
            suggestions = ["Monitor actuals vs forecast."]
        elif score >= 0.75:
            level = "high"
            explanation = "Reliable result. Recommend quick human review."
            suggestions = ["Update model with new data next cycle."]
        elif score >= 0.55:
            level = "moderate"
            explanation = "Reasonable result. Validate key assumptions."
            suggestions = ["Check for missing external regressors."]
        elif score >= 0.40:
            level = "low"
            explanation = "Uncertain result. Expert review required."
            suggestions = ["Time series may be highly volatile."]
        else:
            level = "uncertain"
            explanation = "Do not act. Collect more data first."
            suggestions = ["Insufficient data for forecasting."]

        basis = [f"Prophet MAE: {prophet_mae:.2f}", f"ARIMA MAE: {arima_mae:.2f}"]
        
        return ConfidenceScore(
            score=score,
            level=level,
            explanation=explanation,
            basis=basis,
            suggestions=suggestions
        )

    def forecast(self, data: List[Dict[str, Any]], date_col: str, value_col: str, periods: int = 6) -> Dict[str, Any]:
        try:
            df = route_data(data)
            
            if date_col not in df.columns or value_col not in df.columns:
                raise ValueError(f"Columns {date_col} and/or {value_col} not found.")
                
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(by=date_col)
            
            inferred_freq = pd.infer_freq(df[date_col])
            freq = inferred_freq if inferred_freq else 'MS'
            
            # Splitting for validation (last 20%)
            val_size = max(1, int(len(df) * 0.2))
            train = df.iloc[:-val_size]
            val = df.iloc[-val_size:]
            
            # Prophet
            df_prophet = train[[date_col, value_col]].rename(columns={date_col: 'ds', value_col: 'y'})
            m_prophet = Prophet(yearly_seasonality=True, weekly_seasonality=False)
            m_prophet.fit(df_prophet)
            
            future_val = m_prophet.make_future_dataframe(periods=val_size, freq=freq)
            prophet_val_preds = m_prophet.predict(future_val).iloc[-val_size:]['yhat'].values
            prophet_mae = np.mean(np.abs(prophet_val_preds - val[value_col].values))
            
            # ARIMA
            series_train = train.set_index(date_col)[value_col]
            m_arima = pm.auto_arima(series_train, seasonal=False, stepwise=True, suppress_warnings=True)
            arima_val_preds = m_arima.predict(n_periods=val_size)
            arima_mae = np.mean(np.abs(arima_val_preds - val[value_col].values))
            
            # Ensemble weights
            w_prophet = 1.0 / (prophet_mae + 1e-9)
            w_arima = 1.0 / (arima_mae + 1e-9)
            total_w = w_prophet + w_arima
            w_prophet /= total_w
            w_arima /= total_w
            
            # Final Forecast on full data
            df_full_prophet = df[[date_col, value_col]].rename(columns={date_col: 'ds', value_col: 'y'})
            m_prophet.fit(df_full_prophet)
            future = m_prophet.make_future_dataframe(periods=periods, freq=freq)
            prophet_full_preds = m_prophet.predict(future).iloc[-periods:]
            
            series_full = df.set_index(date_col)[value_col]
            m_arima_full = pm.auto_arima(series_full, seasonal=False, stepwise=True, suppress_warnings=True)
            arima_full_preds, arima_conf = m_arima_full.predict(n_periods=periods, return_conf_int=True)
            
            forecast = []
            interval_widths = []
            mean_forecast = 0.0
            
            for i in range(periods):
                p_val = prophet_full_preds.iloc[i]['yhat']
                p_lower = prophet_full_preds.iloc[i]['yhat_lower']
                p_upper = prophet_full_preds.iloc[i]['yhat_upper']
                
                a_val = arima_full_preds.iloc[i]
                a_lower = arima_conf[i][0]
                a_upper = arima_conf[i][1]
                
                ens_val = p_val * w_prophet + a_val * w_arima
                ens_lower = p_lower * w_prophet + a_lower * w_arima
                ens_upper = p_upper * w_prophet + a_upper * w_arima
                
                dt = prophet_full_preds.iloc[i]['ds']
                forecast.append({
                    "period": i + 1,
                    "date": dt.strftime("%Y-%m-%d"),
                    "value": float(ens_val),
                    "lower_80": float(ens_lower),
                    "upper_80": float(ens_upper)
                })
                interval_widths.append(float(ens_upper - ens_lower))
                mean_forecast += float(ens_val)
                
            mean_forecast /= periods
            
            # Trend detection
            last_3_actual = df[value_col].iloc[-3:].mean()
            if mean_forecast > last_3_actual * 1.02:
                trend_dir = "upward"
                trend_exp = "Forecast suggests an upward trend compared to recent actuals."
            elif mean_forecast < last_3_actual * 0.98:
                trend_dir = "downward"
                trend_exp = "Forecast suggests a downward trend compared to recent actuals."
            else:
                trend_dir = "stable"
                trend_exp = "Forecast suggests stable values compared to recent actuals."
                
            confidence = self._compute_confidence(prophet_mae, arima_mae, interval_widths, mean_forecast)
            
            return {
                "model_used": "Prophet + ARIMA Ensemble",
                "forecast": forecast,
                "trend_direction": trend_dir,
                "trend_explanation": trend_exp,
                "confidence": confidence.model_dump()
            }
        except Exception as e:
            return {
                "model_used": "none",
                "forecast": [],
                "trend_direction": "unknown",
                "trend_explanation": f"Engine failed: {str(e)}",
                "confidence": ConfidenceScore(
                    score=0.0,
                    level="uncertain",
                    explanation=f"Engine failed: {str(e)}",
                    basis=["Exception during execution"],
                    suggestions=["Check date and value columns."]
                ).model_dump()
            }
