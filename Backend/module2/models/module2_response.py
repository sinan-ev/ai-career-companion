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

    Attributes:
        overview (Dict[str, Any]): General dataset shape, missing %, duplicates, and memory usage.
        column_types (Dict[str, str]): Detected type per column (numeric/categorical/datetime/boolean/text/id).
        column_reports (Dict[str, Any]): Deep stats per column (mean, std, top values, etc.).
        quality_score (Dict[str, Any]): 0–100 score + grade A/B/C/D/F based on dataset quality.
        warnings (List[Dict[str, Any]]): Data quality issues found along with severity levels.
        summary_for_agent (str): Compact text block fed into the agent_planner prompt.
        correlation (Optional[Dict[str, Any]], optional): Top correlated numeric pairs. Defaults to None.
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
    analytics_dataset  → human-readable values kept intact ("Male"/"Female", raw salary numbers)
    ml_dataset         → fully encoded + scaled (categories become numbers, values normalized)

    Attributes:
        analytics_shape (List[int]): [rows, cols] of the analytics dataset.
        ml_shape (List[int]): [rows, cols] of the ML dataset, may differ if features added/dropped.
        target_column (str): Which column is the label/target (e.g., "Survived", "Price").
        feature_columns (List[str]): All columns used as predictive features.
        dropped_columns (List[str]): Columns removed during processing (e.g., IDs, constants).
        artifact_paths (Dict[str, str]): File paths of saved encoders and scaler.
        was_encoded (bool): True if the encoding step ran.
        was_scaled (bool): True if the scaling step ran.
        dataset_files (Optional[Dict[str, str]], optional): Paths to the exported CSV files. Defaults to None.
        sample_data (Optional[List[Dict[str, Any]]], optional): Preview data for the UI. Defaults to None.
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
    One execution step recorded by core/memory.py.

    The AI agent decides which steps to run (e.g., handle_missing). 
    Each step is logged here as it executes.

    Attributes:
        step (str): The name of the preprocessing step (matches rule_engine.py step names).
        status (str, optional): The outcome of the step ("success", "skipped", "failed"). Defaults to "success".
        details (Optional[str], optional): Optional human-readable note about what happened. Defaults to None.
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

    This object encapsulates all results and artifacts generated by the Module 2 preprocessing pipeline.

    Attributes:
        dataset_info (Dict[str, Any]): Domain, rows, cols passed through from Module 1.
        eda_report (EDAReport): Full EDA analysis containing deep quality and statistical metrics.
        dataset_outputs (DatasetOutputs): Analytics and ML datasets, plus artifact paths.
        pipeline_steps (List[PipelineStep]): Ordered list of AI-chosen steps and their execution results.
        warnings (List[str]): All combined warnings from EDA and pipeline execution.
        module1_summary (str): Module 1's AI-generated domain summary passed through for context.
        generated_at (str): ISO timestamp of when this report was generated.
    """
    dataset_info: Dict[str, Any]          # from module1_output["dataset_info"]
    eda_report: EDAReport
    dataset_outputs: DatasetOutputs
    pipeline_steps: List[PipelineStep]
    warnings: List[str]
    module1_summary: str                  # module1_output["ai_summary"]
    generated_at: str
