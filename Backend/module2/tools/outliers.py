import re
import pandas as pd
import numpy as np
from typing import Tuple, List

# IQR multiplier — 1.5 is standard (same as Module 1's profiler)
IQR_MULTIPLIER = 1.5

# Keywords in column name/meaning that signal we should SKIP outlier handling
SKIP_KEYWORDS = [
    "id", "index", "key", "uuid", "ref", "code",
    "flag", "binary", "indicator", "dummy", "encoded",
    "year", "month", "day",           # date parts — valid range is known
]

# If a column has fewer than this many unique values it's likely
# categorical stored as numeric — skip outlier capping
MIN_UNIQUE_FOR_OUTLIER = 5


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def handle_outliers(
    df: pd.DataFrame,
    module1_output: dict,
    strategy: str = "cap"
) -> Tuple[pd.DataFrame, str]:


    schema       = module1_output.get("data_schema", {})
    col_meanings = module1_output.get("column_meanings", {})
    numeric_cols = schema.get("numeric", [])

    # Only process columns that actually exist in df
    cols_to_check = [c for c in numeric_cols if c in df.columns]

    if not cols_to_check:
        return df, "no numeric columns to check for outliers"

    actions = []
    rows_to_drop = set()

    for col in cols_to_check:
        # Skip columns that shouldn't have outlier capping
        if _should_skip(col, col_meanings):
            continue

        # Skip columns with too few unique values (likely categorical as int)
        if df[col].nunique() < MIN_UNIQUE_FOR_OUTLIER:
            continue

        series = df[col].dropna()
        if len(series) == 0:
            continue

        # Calculate IQR bounds
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        # If IQR is zero the column is nearly constant — skip
        if iqr == 0:
            continue

        lower_fence = q1 - IQR_MULTIPLIER * iqr
        upper_fence = q3 + IQR_MULTIPLIER * iqr

        # Find outliers
        outlier_mask = (df[col] < lower_fence) | (df[col] > upper_fence)
        outlier_count = outlier_mask.sum()

        if outlier_count == 0:
            continue

        if strategy == "cap":
            df[col] = df[col].clip(lower=lower_fence, upper=upper_fence)
            actions.append(
                f"capped '{col}': {outlier_count} outliers clipped to "
                f"[{round(lower_fence, 2)}, {round(upper_fence, 2)}]"
            )

        elif strategy == "remove":
            rows_to_drop.update(df[outlier_mask].index.tolist())
            actions.append(
                f"flagged '{col}': {outlier_count} outlier rows for removal"
            )

    # Drop rows if strategy is remove
    if strategy == "remove" and rows_to_drop:
        before = len(df)
        df = df.drop(index=list(rows_to_drop)).reset_index(drop=True)
        after = len(df)
        actions.append(f"removed {before - after} rows total")

    # Build detail message
    if actions:
        detail = f"{len(actions)} outlier actions: " + "; ".join(actions)
    else:
        detail = "no outliers detected in any numeric column"

    return df, detail


# ─────────────────────────────────────────────
#  DETECTION ONLY (no modification)
# ─────────────────────────────────────────────

def detect_outliers(df: pd.DataFrame, module1_output: dict) -> dict:
    """
    Detect outliers without modifying the DataFrame.
    Returns a summary dict — used by agent_planner to decide
    if handle_outliers step is needed at all.

    Returns:
        {
            "col_name": {
                "outlier_count": 14,
                "outlier_percent": 5.71,
                "lower_fence": 12.5,
                "upper_fence": 68.3
            },
            ...
        }
    """
    schema       = module1_output.get("data_schema", {})
    col_meanings = module1_output.get("column_meanings", {})
    numeric_cols = schema.get("numeric", [])

    result = {}

    for col in numeric_cols:
        if col not in df.columns:
            continue
        if _should_skip(col, col_meanings):
            continue
        if df[col].nunique() < MIN_UNIQUE_FOR_OUTLIER:
            continue

        series = df[col].dropna()
        if len(series) == 0:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_fence = q1 - IQR_MULTIPLIER * iqr
        upper_fence = q3 + IQR_MULTIPLIER * iqr

        outlier_mask  = (series < lower_fence) | (series > upper_fence)
        outlier_count = int(outlier_mask.sum())

        if outlier_count > 0:
            result[col] = {
                "outlier_count":   outlier_count,
                "outlier_percent": round(outlier_count / len(series) * 100, 2),
                "lower_fence":     round(float(lower_fence), 4),
                "upper_fence":     round(float(upper_fence), 4),
                "min_value":       round(float(series.min()), 4),
                "max_value":       round(float(series.max()), 4),
            }

    return result


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _should_skip(col_name: str, col_meanings: dict) -> bool:
    """
    Decide if a column should be skipped for outlier handling.

    Skips:
    - ID/index columns (PassengerId, user_id) — these aren't real values
    - Binary/flag columns — 0 and 1 are valid, not outliers
    - Date part columns (year, month) — bounded by definition
    """
    text = f"{col_name.lower()} {col_meanings.get(col_name, '').lower()}"
    return any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in SKIP_KEYWORDS)    
