

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
    Sequentially executes the steps in the provided preprocessing plan.
    
    Ensures that steps are run in a canonical order regardless of the plan's specific sequencing, 
    and captures all generated artifacts and operation statuses.

    Args:
        df (pd.DataFrame): The validated input DataFrame.
        plan (List[str]): List of tool step names provided by the AI planner or fallback.
        module1_output (Dict[str, Any]): Full context dictionary output from Module 1.
        memory (PipelineMemory): The memory instance used for detailed logging.
        target_col (str, optional): The identified target column, if any. Defaults to None.
        outlier_strategy (str, optional): Strategy for outlier handling ("cap" or "remove"). Defaults to "cap".
        is_classification (bool, optional): Indicates if the task is a classification task. Defaults to True.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any], List[Tuple[str, str, str]]]: 
            A tuple containing the transformed DataFrame, a dictionary of ML artifacts, and a list of step execution summaries.
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
    Routes a single planned step name to its corresponding data transformation tool.
    
    Args:
        step (str): The specific step name (e.g., 'encoding').
        df (pd.DataFrame): The current state of the dataset.
        module1_output (Dict[str, Any]): Context dictionary from Module 1.
        artifacts (Dict[str, Any]): Cumulative dictionary to store newly generated artifacts.
        target_col (Optional[str]): The dataset's target column.
        outlier_strategy (str): Chosen strategy to handle outliers.
        is_classification (bool): Whether the machine learning task is classification.
        
    Returns:
        Tuple[pd.DataFrame, str]: The newly transformed DataFrame and an operational summary note.
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
