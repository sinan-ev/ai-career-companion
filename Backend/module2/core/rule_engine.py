

import traceback
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from module2.core.memory import PipelineMemory
from module2.tools.cleaning          import handle_missing
from module2.tools.outliers          import handle_outliers
from module2.tools.features          import engineer_features
from module2.tools.encoding          import encode_categoricals
from module2.tools.scaling           import scale_features
from module2.tools.feature_selection import select_features


# ─────────────────────────────────────────────────────────────────────────────
# Canonical step order — the rule engine always runs steps in this sequence
# regardless of what order the agent listed them.
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_ORDER = [
    "remove_duplicates",    # 1. clean first
    "handle_missing",       # 2. nulls
    "handle_outliers",      # 3. outliers
    "feature_engineering",  # 4. create new columns
    "encoding",             # 5. strings → numbers
    "scaling",              # 6. normalize
    "feature_selection",    # 7. drop noise
]

# Human-readable names for logging
STEP_LABELS = {
    "remove_duplicates":  "Remove Duplicate Rows",
    "handle_missing":     "Handle Missing Values",
    "handle_outliers":    "Handle Outliers",
    "feature_engineering":"Feature Engineering",
    "encoding":           "Encode Categorical Columns",
    "scaling":            "Scale Numeric Features",
    "feature_selection":  "Feature Selection",
}


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def execute_plan(
    df: pd.DataFrame,
    plan: List[str],
    module1_output: Dict[str, Any],
    memory: PipelineMemory,
    target_col: str = None,
    outlier_strategy: str = "cap",
    is_classification: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any], List[Tuple[str, str, str]]]:
    """
    Execute the agent's plan step by step.

    Parameters
    ----------
    df               : validated input DataFrame
    plan             : list of step names from the AI agent
    module1_output   : full Module 1 output dict
    memory           : PipelineMemory instance for logging
    target_col       : target column — passed to every tool
    outlier_strategy : "cap" or "remove" — passed to handle_outliers
    is_classification: True for classification, False for regression

    Returns
    -------
    df_out           : transformed DataFrame
    artifacts        : dict of saved encoders/scalers/feature info
    steps_summary    : [(step_name, status, note), ...]
    """

    # Normalise plan — lowercase, strip whitespace, drop unknowns
    known_steps   = set(CANONICAL_ORDER)
    requested     = set()
    unknown_steps = []

    for s in plan:
        s_clean = s.strip().lower()
        if s_clean in known_steps:
            requested.add(s_clean)
        else:
            unknown_steps.append(s_clean)

    if unknown_steps:
        memory.log_warning(f"Unknown step names in plan (skipped): {unknown_steps}")

    # Artifact collectors
    artifacts: Dict[str, Any] = {
        "encoder_map":    {},
        "scaler_map":     {},
        "features_added": [],
        "dropped_cols":   {},
    }

    # Build the ordered execution list — only steps the agent requested
    steps_to_run = [s for s in CANONICAL_ORDER if s in requested]

    if not steps_to_run:
        memory.log_warning("Agent plan contained no valid steps — returning input unchanged")
        return df.copy(), artifacts, []

    df_current   = df.copy()
    steps_summary: List[Tuple[str, str, str]] = []

    # ── Execute each step ────────────────────────────────────────────────────
    for step in steps_to_run:
        label = STEP_LABELS[step]
        memory.start_step(step)

        try:
            df_current, note = _run_step(
                step             = step,
                df               = df_current,
                module1_output   = module1_output,
                artifacts        = artifacts,
                target_col       = target_col,
                outlier_strategy = outlier_strategy,
                is_classification= is_classification,
            )
            memory.end_step(step, details=note)
            steps_summary.append((step, "success", note))

        except Exception as e:
            error_detail = f"{type(e).__name__}: {e}"
            tb           = traceback.format_exc()
            memory.fail_step(step, error=error_detail)
            steps_summary.append((step, "failed", error_detail))
            # Pipeline continues — one broken step doesn't stop everything
            continue

    return df_current, artifacts, steps_summary


# ─────────────────────────────────────────────────────────────────────────────
# Per-step router
# ─────────────────────────────────────────────────────────────────────────────

def _run_step(
    step             : str,
    df               : pd.DataFrame,
    module1_output   : Dict[str, Any],
    artifacts        : Dict[str, Any],
    target_col       : Optional[str],
    outlier_strategy : str,
    is_classification: bool,
) -> Tuple[pd.DataFrame, str]:
    """
    Route a single step name to the correct tool.
    Returns (transformed_df, note_string).
    """

    if step == "remove_duplicates":
        # remove_duplicates is often handled inside handle_missing, 
        # but if called explicitly, we do it here
        before = len(df)
        df_out = df.drop_duplicates().reset_index(drop=True)
        count = before - len(df_out)
        return df_out, f"Removed {count} duplicated rows"

    elif step == "handle_missing":
        df_out, note = handle_missing(
            df             = df,
            module1_output = module1_output,
        )
        return df_out, note

    elif step == "handle_outliers":
        df_out, note = handle_outliers(
            df             = df,
            module1_output = module1_output,
            strategy       = outlier_strategy,
        )
        return df_out, note

    elif step == "feature_engineering":
        df_out, features_added, note = engineer_features(
            df             = df,
            module1_output = module1_output,
            target_col     = target_col,
        )
        artifacts["features_added"].extend(features_added)
        return df_out, note

    elif step == "encoding":
        df_out, encoder_map, encoding_log, note = encode_categoricals(
            df             = df,
            module1_output = module1_output,
            target_col     = target_col,
        )
        artifacts["encoder_map"].update(encoder_map)
        return df_out, note

    elif step == "scaling":
        df_out, scaler_map, scaling_log, note = scale_features(
            df             = df,
            module1_output = module1_output,
            target_col     = target_col,
        )
        artifacts["scaler_map"].update(scaler_map)
        return df_out, note

    elif step == "feature_selection":
        df_out, kept_cols, dropped_cols, note = select_features(
            df             = df,
            module1_output = module1_output,
            target_col     = target_col,
        )
        artifacts["dropped_cols"].update(dropped_cols)
        return df_out, note

    else:
        raise ValueError(f"No tool mapped for step '{step}'")
