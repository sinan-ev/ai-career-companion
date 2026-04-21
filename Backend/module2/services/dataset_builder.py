"""
services/dataset_builder.py
============================
Builds two purpose-built datasets from the processed DataFrame.

WHY TWO DATASETS?
─────────────────
After the pipeline runs, we have one fully processed DataFrame.
But different consumers need different things:

analytics_dataset  → for humans (dashboards, reports, charts)
                     - Original readable values kept (Male/Female, not 0/1)
                     - Raw numeric values (not scaled to 0–1)
                     - Use for: Tableau, Power BI, pandas analysis

ml_dataset         → for models (sklearn, XGBoost, neural nets)
                     - Everything encoded to numbers
                     - Everything scaled to consistent range
                     - Target column separated
                     - Use for: model.fit(X, y)

CONNECTION TO MODULE 1
──────────────────────
module1_output["data_schema"]
    → tells us which columns were originally categorical
    → analytics dataset keeps those in original form

module1_output["column_meanings"]
    → used by target_detector to find the target column

module1_output["data_quality"]["total_rows"]
    → sanity check — output row count should match or be close

HOW IT WORKS
────────────
1. analytics_dataset = df_before_encoding (snapshot taken before encoding step)
   - We drop ID/unknown columns using target_detector.get_feature_columns()
   - We keep the target column

2. ml_dataset = df_after_full_pipeline (already encoded + scaled)
   - Drop ID/unknown/dropped columns
   - Keep target column
   - Split into X (features) and y (target) metadata

USAGE (in pipeline_module2.py)
──────────────────────────────
    from module2.services.dataset_builder import build_datasets

    result = build_datasets(
        df_analytics   = df_before_encoding,  # snapshot before encoding
        df_ml          = df_processed,        # fully processed
        module1_output = module1_output,
        artifacts      = artifacts,           # from rule_engine
    )
"""

import pandas as pd
from typing import Dict, Any, Tuple

from module2.services.target_detector import detect_target, get_feature_columns


def build_datasets(
    df_analytics: pd.DataFrame,
    df_ml: pd.DataFrame,
    module1_output: dict,
    artifacts: dict,
) -> Dict[str, Any]:
    """
    Build analytics and ML-ready datasets from the processed DataFrames.

    Args:
        df_analytics   : Snapshot of df BEFORE encoding (human-readable)
        df_ml          : Fully processed df (encoded + scaled)
        module1_output : Full Module 1 output dict
        artifacts      : From rule_engine — encoder_map, scaler_map, dropped_columns

    Returns:
        {
            "analytics_dataset":  pd.DataFrame,
            "ml_dataset":         pd.DataFrame,
            "target_column":      str,
            "feature_columns":    List[str],
            "dropped_columns":    List[str],
            "analytics_shape":    [rows, cols],
            "ml_shape":           [rows, cols],
            "was_encoded":        bool,
            "was_scaled":         bool,
            "target_stats":       dict,
        }
    """
    col_meanings   = module1_output.get("column_meanings", {})
    schema         = module1_output.get("data_schema", {})
    dropped_cols   = artifacts.get("dropped_columns", [])
    encoder_map    = artifacts.get("encoder_map", {})
    scaler_map     = artifacts.get("scaler_map", {})

    # ── Detect target column ──
    target_col, detection_method, confidence = detect_target(
        df_ml.columns.tolist(), module1_output
    )

    # ── Get feature / drop split from ML dataset columns ──
    feature_cols, id_cols_to_drop = get_feature_columns(
        df_ml.columns.tolist(), target_col, module1_output
    )

    # Combine all columns to drop
    all_dropped = list(set(dropped_cols + id_cols_to_drop))

    # ── Build ANALYTICS dataset ──
    # Keep: all original columns except ID/unknown cols and pipeline-dropped cols
    analytics_keep = [
        c for c in df_analytics.columns
        if c not in all_dropped
    ]
    analytics_df = df_analytics[analytics_keep].copy()

    # ── Build ML dataset ──
    # Keep: feature columns + target column, drop IDs and pipeline-dropped
    ml_keep = [
        c for c in df_ml.columns
        if c not in all_dropped
    ]
    ml_df = df_ml[ml_keep].copy()

    # ── Compute target stats (helpful for agent summary) ──
    target_stats = _compute_target_stats(ml_df, target_col)

    # ── Final column lists ──
    final_feature_cols = [c for c in ml_df.columns if c != target_col]

    return {
        "analytics_dataset":  analytics_df,
        "ml_dataset":         ml_df,
        "target_column":      target_col,
        "target_detection":   detection_method,
        "target_confidence":  confidence,
        "feature_columns":    final_feature_cols,
        "dropped_columns":    all_dropped,
        "analytics_shape":    list(analytics_df.shape),
        "ml_shape":           list(ml_df.shape),
        "was_encoded":        len(encoder_map) > 0,
        "was_scaled":         len(scaler_map) > 0,
        "target_stats":       target_stats,
    }


def _compute_target_stats(df: pd.DataFrame, target_col: str) -> dict:
    """
    Compute basic statistics about the target column.
    Helps the agent and user understand what kind of problem this is.
    """
    if target_col not in df.columns:
        return {}

    series    = df[target_col].dropna()
    n_unique  = series.nunique()
    is_classification = n_unique <= 20

    stats = {
        "n_unique":          int(n_unique),
        "is_classification": is_classification,
        "is_regression":     not is_classification,
        "missing_count":     int(df[target_col].isnull().sum()),
    }

    if is_classification:
        # Classification: show class distribution
        value_counts = series.value_counts()
        stats["class_distribution"] = {
            str(k): int(v) for k, v in value_counts.items()
        }
        stats["class_balance_pct"] = {
            str(k): round(v / len(series) * 100, 2)
            for k, v in value_counts.items()
        }
        # Flag imbalanced datasets (minority class < 20%)
        min_class_pct = min(v / len(series) * 100 for v in value_counts.values)
        stats["is_imbalanced"] = min_class_pct < 20.0
    else:
        # Regression: show distribution summary
        stats["mean"]   = round(float(series.mean()), 4)
        stats["median"] = round(float(series.median()), 4)
        stats["std"]    = round(float(series.std()), 4)
        stats["min"]    = round(float(series.min()), 4)
        stats["max"]    = round(float(series.max()), 4)

    return stats
