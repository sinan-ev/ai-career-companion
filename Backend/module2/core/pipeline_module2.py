
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.gcs_storage import save_csv

from module2.core.validator import validate_or_raise, ValidationError
from module2.core.memory import Memory
from module2.core.agent_planner import generate_plan
from module2.core.rule_engine import execute_plan
from module2.tools.eda import generate_eda
from module2.services.dataset_builder import build_datasets
from module2.services.artifact_manager import save_artifacts

from module2.models.module2_response import (
    Module2Response,
    EDAReport,
    DatasetOutputs,
    PipelineStep,
)


def run_module2(
    df: pd.DataFrame,
    module1_output: dict,
    groq_api_key: Optional[str] = None,
    save_artifacts_to: str = "artifacts",
) -> Module2Response:
    """
    Executes the complete Module 2 preprocessing pipeline, which includes validation, EDA, planning, 
    transformation, and dataset artifact generation.

    Args:
        df (pd.DataFrame): The pandas DataFrame to process.
        module1_output (dict): The dictionary output from Module 1 containing schema and metadata.
        groq_api_key (Optional[str], optional): API key for the Groq service. Defaults to None.
        save_artifacts_to (str, optional): Directory to save resulting ML artifacts (like encoders). Defaults to "artifacts".

    Returns:
        Module2Response: A fully structured Pydantic response containing EDA reports, processing steps, 
                         dataset summaries, and file paths.
    """

    # STEP 1 --- VALIDATE INPUTS
 
    validation_warnings = validate_or_raise(df, module1_output)

    # STEP 2 --- DEEP EDA
  
    eda_report, eda_summary = generate_eda(df, module1_output)

    # STEP 3 --- AI PLANS THE PIPELINE

    plan = generate_plan(
        module1_output = module1_output,
        eda_report     = eda_report,
        groq_api_key   = groq_api_key,
    )

    # STEP 4 --- DETECT TARGET COLUMN

    from module2.services.target_detector import detect_target
    target_col, target_method, target_conf = detect_target(list(df.columns), module1_output)

    # STEP 5 --- SNAPSHOT FOR ANALYTICS DATASET

    df_analytics_snapshot = df.copy(deep=True)

    # STEP 6 — EXECUTE THE PLAN

    memory = Memory()
    df_processed, artifacts, pipeline_steps_log = execute_plan(
        df               = df,
        plan             = plan,
        module1_output   = module1_output,
        memory           = memory,
        target_col       = target_col,
    )

    # STEP 6 — BUILD TWO DATASETS

    dataset_result = build_datasets(
        df_analytics   = df_analytics_snapshot,
        df_ml          = df_processed,
        module1_output = module1_output,
        artifacts      = artifacts,
    )

    # STEP 7 — SAVE ARTIFACTS


    artifact_paths = save_artifacts(
        encoder_map    = artifacts["encoder_map"],
        scaler_map     = artifacts["scaler_map"],
        feature_cols   = dataset_result["feature_columns"],
        module1_output = module1_output,
        base_dir       = save_artifacts_to,
    )

    # ══════════════════════════════════════════
    # STEP 8 — ASSEMBLE MODULE2RESPONSE
    # ══════════════════════════════════════════

    # — EDAReport model —
    eda_report_model = EDAReport(
        overview         = eda_report["overview"],
        column_types     = eda_report["column_types"],
        column_reports   = eda_report["column_reports"],
        quality_score    = eda_report["quality_score"],
        warnings         = eda_report["warnings"],
        summary_for_agent = eda_report["summary_for_agent"],
        correlation      = eda_report.get("correlation"),
    )

    # — DatasetOutputs model —
    dataset_outputs_model = DatasetOutputs(
        analytics_shape  = dataset_result["analytics_shape"],
        ml_shape         = dataset_result["ml_shape"],
        target_column    = dataset_result["target_column"],
        feature_columns  = dataset_result["feature_columns"],
        dropped_columns  = dataset_result["dropped_columns"],
        artifact_paths   = {
            "encoders":  artifact_paths.get("encoders", ""),
            "scalers":   artifact_paths.get("scalers", ""),
            "metadata":  artifact_paths.get("metadata", ""),
            "base_dir":  artifact_paths.get("base_dir", ""),
        },
        was_encoded      = dataset_result["was_encoded"],
        was_scaled       = dataset_result["was_scaled"],
        dataset_files    = None, # Will be filled below
    )

    # ══════════════════════════════════════════
    # STEP 7.5 — EXPORT DATASETS TO CSV
    # ══════════════════════════════════════════
    # Save the processed dataframes to disk if export_dir is provided
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = module1_output.get("dataset_info", {}).get("file_name", "dataset")
    base_name = Path(base_name).stem
    
    analytics_filename = f"{base_name}_{timestamp}_analytics.csv"
    ml_filename        = f"{base_name}_{timestamp}_ml.csv"
    
    save_csv(dataset_result["analytics_dataset"], f"exports/{analytics_filename}")
    save_csv(dataset_result["ml_dataset"], f"exports/{ml_filename}")
    
    dataset_outputs_model.dataset_files = {
        "analytics": analytics_filename,
        "ml": ml_filename
    }

    # Extract sample data for UI preview (first 10 rows)
    # We use analytics_dataset as it is more readable for humans
    sample_df = dataset_result["analytics_dataset"].head(10)
    dataset_outputs_model.sample_data = sample_df.where(pd.notnull(sample_df), None).to_dict("records")

    # — Pipeline steps from memory —
    pipeline_steps = memory.get_steps()

    # — Combine all warnings —
    all_warnings = list(validation_warnings) + [
        w.get("message", str(w))
        for w in eda_report.get("warnings", [])
        if w.get("level") in ("critical", "high")
    ]

    # — Final response —
    response = Module2Response(
        dataset_info     = module1_output.get("dataset_info", {}),
        eda_report       = eda_report_model,
        dataset_outputs  = dataset_outputs_model,
        pipeline_steps   = pipeline_steps,
        warnings         = all_warnings,
        module1_summary  = module1_output.get("ai_summary", ""),
        generated_at     = datetime.now().isoformat(),
    )

    # Print summary to console (useful in development)
    _print_summary(response, memory, dataset_result)

    return response


# ─────────────────────────────────────────────
#  CONSOLE SUMMARY (development helper)
# ─────────────────────────────────────────────

def _print_summary(
    response: Module2Response,
    memory: Memory,
    dataset_result: dict,
) -> None:
    """
    Prints a cleanly formatted execution summary of Module 2 to the console.
    
    Args:
        response (Module2Response): The finalized response model.
        memory (Memory): The execution memory that logged pipeline steps.
        dataset_result (dict): The final outputs returned by dataset builder.
    """
    sep = "=" * 50
    print(f"\n{sep}")
    print("  MODULE 2 — PIPELINE COMPLETE")
    print(sep)
    print(f"  Domain:          {response.dataset_info.get('domain', '?')}")
    print(f"  Quality grade:   {response.eda_report.quality_score.get('grade')} "
          f"({response.eda_report.quality_score.get('score')}/100)")
    print(f"  Target column:   {response.dataset_outputs.target_column} "
          f"(via {dataset_result.get('target_detection', '?')}, "
          f"conf={dataset_result.get('target_confidence', '?')})")
    print(f"  Analytics shape: {response.dataset_outputs.analytics_shape}")
    print(f"  ML shape:        {response.dataset_outputs.ml_shape}")
    print(f"  Was encoded:     {response.dataset_outputs.was_encoded}")
    print(f"  Was scaled:      {response.dataset_outputs.was_scaled}")
    print(f"  Dropped columns: {response.dataset_outputs.dropped_columns}")
    print(f"  Artifacts saved: {response.dataset_outputs.artifact_paths.get('base_dir')}")
    print()
    print(memory.get_summary())
    if response.warnings:
        print()
        print("  Warnings:")
        for w in response.warnings:
            print(f"    - {w}")
    print(sep)
