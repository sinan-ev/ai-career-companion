from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    """
    Generates structured plain-text and JSON reports from the engine execution state.
    """
    def generate(self, state: Dict[str, Any]) -> str:
        """
        Generates a detailed, human-readable plain-text executive report summarizing all analysis results.

        Args:
            state (Dict[str, Any]): The execution state containing predictions, forecasts,
                root cause analysis, risks, recommendations, and decisions, along with confidences.

        Returns:
            str: The formatted plain-text decision intelligence report.
        """
        job_id = state.get("job_id", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        overall_conf = state.get("overall_confidence", {})
        overall_score = overall_conf.get("score", 0.0)
        overall_level = overall_conf.get("level", "uncertain")
        limiting_factor = overall_conf.get("explanation", "").split(" limited by ")[-1].replace(" engine.", "") if " limited by " in overall_conf.get("explanation", "") else "Unknown"
        suggestions = "\n".join([f"    - {s}" for s in overall_conf.get("suggestions", [])])

        # Section 1: Predictions
        pred = state.get("prediction_result") or {}
        pred_conf = pred.get("confidence", {})
        section_1 = f"""
    ── SECTION 1: PREDICTIONS ──────────────────
    Model: {pred.get('model_used', 'N/A')}
    Task: {pred.get('task_type', 'N/A')}
    CV Score: {pred.get('cv_score', 0.0):.4f} if isinstance({pred.get('cv_score', 0.0)}, float) else {pred.get('cv_score', 0.0)}
    Confidence: {pred_conf.get('level', 'N/A')} ({pred_conf.get('score', 0.0):.2f})"""

        # Section 2: Forecast
        forecast = state.get("forecast_result")
        if forecast:
            fc_conf = forecast.get("confidence", {})
            section_2 = f"""
    ── SECTION 2: FORECAST ─────────────────────
    Trend: {forecast.get('trend_direction', 'N/A')}
    {forecast.get('trend_explanation', 'N/A')}
    Confidence: {fc_conf.get('level', 'N/A')} ({fc_conf.get('score', 0.0):.2f})"""
        else:
            section_2 = """
    ── SECTION 2: FORECAST ─────────────────────
    (skip if no forecast)"""

        # Section 3: RCA
        rca = state.get("rca_result") or {}
        rca_conf = rca.get("confidence", {})
        top_causes = "\n".join([f"      {i+1}. {f['feature']} — {f['direction']} outcome (SHAP: {f['shap_value']:.4f})" for i, f in enumerate(rca.get("top_features", []))])
        section_3 = f"""
    ── SECTION 3: ROOT CAUSE ANALYSIS ──────────
    Top Root Causes:
{top_causes}
    {rca.get('explanation', 'N/A')}
    Confidence: {rca_conf.get('level', 'N/A')} ({rca_conf.get('score', 0.0):.2f})"""

        # Section 4: Risk Assessment
        risk = state.get("risk_result") or {}
        risk_conf = risk.get("confidence", {})
        alerts = "\n    ".join(risk.get("alerts", []))
        section_4 = f"""
    ── SECTION 4: RISK ASSESSMENT ──────────────
    Risk Score: {risk.get('risk_score', 0.0):.1f}/100
    Anomalies Found: {risk.get('anomaly_count', 0)} / {risk.get('total_records', 0)}
    {alerts}
    Confidence: {risk_conf.get('level', 'N/A')} ({risk_conf.get('score', 0.0):.2f})"""

        # Section 5: Recommendations
        rec = state.get("recommendation_result") or {}
        rec_conf = rec.get("confidence", {})
        recs_list = "\n".join([f"      [{r['priority']}] {r['action']}" for r in rec.get("recommendations", [])])
        section_5 = f"""
    ── SECTION 5: RECOMMENDATIONS ──────────────
{recs_list}"""

        # Section 6: Decision
        dec = state.get("decision_result") or {}
        dec_conf = dec.get("confidence", {})
        action_plan = "\n".join([f"      {step}" for step in dec.get("action_plan", [])])
        section_6 = f"""
    ── SECTION 6: STRATEGIC DECISION ───────────
    Situation : {dec.get('situation', 'N/A')}
    Finding   : {dec.get('key_finding', 'N/A')}
    Decision  : {dec.get('strategic_decision', 'N/A')}

    Action Plan:
{action_plan}

    Executive Summary:
    {dec.get('executive_summary', 'N/A')}"""

        # Confidence Breakdown
        breakdown = f"""
    ── CONFIDENCE BREAKDOWN ────────────────────
    Prediction  : {pred_conf.get('score', 0.0):.2f} ({pred_conf.get('level', 'N/A')})
    Forecast    : {fc_conf.get('score', 0.0):.2f} ({fc_conf.get('level', 'N/A')}) if forecast else N/A
    RCA         : {rca_conf.get('score', 0.0):.2f} ({rca_conf.get('level', 'N/A')})
    Risk        : {risk_conf.get('score', 0.0):.2f} ({risk_conf.get('level', 'N/A')})
    Recommend   : {rec_conf.get('score', 0.0):.2f} ({rec_conf.get('level', 'N/A')})
    Decision    : {dec_conf.get('score', 0.0):.2f} ({dec_conf.get('level', 'N/A')})
    ─────────────────────────────────────────────
    OVERALL     : {overall_score:.2f} ({overall_level})
    Limiting factor: {limiting_factor}"""

        report = f"""
    ═══════════════════════════════════════════
    MODULE 3B — AI DECISION INTELLIGENCE REPORT
    ═══════════════════════════════════════════
    Job ID        : {job_id}
    Generated at  : {timestamp}
    Overall Confidence : {overall_score:.2f} ({overall_level})
{section_1}
{section_2}
{section_3}
{section_4}
{section_5}
{section_6}
{breakdown}

    ── IMPROVEMENT SUGGESTIONS ─────────────────
{suggestions}
    ═══════════════════════════════════════════
    """
        return report

    def generate_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts and structures all execution outputs from the state into a clean JSON-serializable dictionary.

        Args:
            state (Dict[str, Any]): The active pipeline execution state.

        Returns:
            Dict[str, Any]: A dictionary detailing predictions, forecasts, RCA, risk assessment,
                recommendations, and final strategic decisions.
        """
        return {
            "job_id": state.get("job_id"),
            "prediction": state.get("prediction_result"),
            "forecast": state.get("forecast_result"),
            "rca": state.get("rca_result"),
            "risk": state.get("risk_result"),
            "recommendation": state.get("recommendation_result"),
            "decision": state.get("decision_result"),
            "overall_confidence": state.get("overall_confidence"),
            "errors": state.get("errors", [])
        }
