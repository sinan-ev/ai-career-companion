"""
models/module2_response.py
==========================
Pydantic output models for Module 2.

This is the CONTRACT — the exact shape of what run_module2() returns.
Every other file in Module 2 builds toward this.

Connection to Module 1
──────────────────────
Module 1 returns AnalysisResponse with 7 fields:
    dataset_info, schema, column_meanings,
    data_quality, ai_summary, suggested_analyses, warnings

Module 2 receives that full object as `module1_output` and produces
Module2Response — a richer object that adds:
    - EDA report (deeper than Module 1's data_quality)
    - Two processed datasets (analytics + ML-ready)
    - Pipeline steps the AI chose to run
    - Saved artifacts (encoders, scaler) for production use
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────
#  SUB-MODEL 1 — EDA Report
# ─────────────────────────────────────────────

class EDAReport(BaseModel):
    """
    Deep EDA analysis produced by tools/eda.py.

    Built ON TOP of Module 1's data_quality — not a replacement.
    Module 1 gives us: missing counts, duplicate rows, basic stats.
    We add:           skewness, outliers, correlations, quality score,
                      per-column type analysis, agent-ready summary.

    Fields
    ──────
    overview         → shape, missing %, duplicates, memory usage
    column_types     → detected type per column (numeric/categorical/
                       datetime/boolean/text/id)
    column_reports   → deep stats per column (mean, std, top values, etc.)
    correlation      → top correlated numeric pairs
    quality_score    → 0–100 score + grade A/B/C/D/F
    warnings         → data quality issues found (with severity levels)
    summary_for_agent → compact text block fed into agent_planner prompt
    """
    overview: Dict[str, Any]
    column_types: Dict[str, str]
    column_reports: Dict[str, Any]
    quality_score: Dict[str, Any]
    warnings: List[Dict[str, Any]]
    summary_for_agent: str
    correlation: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
#  SUB-MODEL 2 — Dataset Outputs
# ─────────────────────────────────────────────

class DatasetOutputs(BaseModel):
    """
    The two datasets produced by services/dataset_builder.py.

    WHY TWO DATASETS?
    ─────────────────
    analytics_dataset  → human-readable values kept intact
                         ("Male"/"Female", raw salary numbers)
                         → use for dashboards, reports, charts

    ml_dataset         → fully encoded + scaled
                         (categories become numbers, values normalized)
                         → feed directly into sklearn, XGBoost, etc.

    artifact_paths     → file paths of saved encoders + scaler (.pkl)
                         → needed later to DECODE predictions back to
                           human-readable values in production

    target_column      → which column is the label/target
                         (detected by services/target_detector.py
                          using Module 1's schema + column_meanings)
    """
    analytics_shape: List[int]       # [rows, cols]
    ml_shape: List[int]              # [rows, cols] — may differ if features added
    target_column: str               # e.g. "Survived", "Price", "Churn"
    feature_columns: List[str]       # all columns used as features (not target)
    dropped_columns: List[str]       # columns removed (constants, IDs, all-null)
    artifact_paths: Dict[str, str]   # {"encoders": "...", "scaler": "..."}
    was_encoded: bool                # True if encoding step ran
    was_scaled: bool                 # True if scaling step ran
    dataset_files: Optional[Dict[str, str]] = None # {"analytics": "path/to/csv", "ml": "path/to/csv"}
    sample_data: Optional[List[Dict[str, Any]]] = None # UI data preview


# ─────────────────────────────────────────────
#  SUB-MODEL 3 — Pipeline Step
# ─────────────────────────────────────────────

class PipelineStep(BaseModel):
    """
    One step recorded by core/memory.py.

    The AI agent decides which steps to run (e.g. handle_missing,
    encoding, scaling). Each step is logged here as it executes.

    step     → step name (matches rule_engine.py step names)
    status   → "success" | "skipped" | "failed"
    details  → optional human-readable note about what happened
               e.g. "imputed 23 missing values in Age using median"
    """
    step: str
    status: str = "success"
    details: Optional[str] = None


# ─────────────────────────────────────────────
#  TOP-LEVEL RESPONSE
# ─────────────────────────────────────────────

class Module2Response(BaseModel):
    """
    The complete output of run_module2().

    This is what gets returned to the API route, or to Module 3
    when we build it later.

    dataset_info    → passed through from Module 1 (domain, rows, cols)
    eda_report      → full EDA analysis (deeper than Module 1's quality)
    dataset_outputs → two datasets + artifact paths + column info
    pipeline_steps  → ordered list of AI-chosen steps + their results
    warnings        → all warnings combined (EDA + processing)
    module1_summary → Module 1's ai_summary passed through for context
    generated_at    → ISO timestamp
    """
    dataset_info: Dict[str, Any]          # from module1_output["dataset_info"]
    eda_report: EDAReport
    dataset_outputs: DatasetOutputs
    pipeline_steps: List[PipelineStep]
    warnings: List[str]
    module1_summary: str                  # module1_output["ai_summary"]
    generated_at: str
