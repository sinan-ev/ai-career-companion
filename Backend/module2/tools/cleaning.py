
# Handles missing values and duplicate rows.

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any

# Columns whose meanings suggest skewed distributions → use median
SKEWED_MEANING_KEYWORDS = [
    "age", "salary", "income", "fare", "price", "cost",
    "revenue", "sales", "amount", "wage", "fee", "rent"
]

# Threshold: drop column if missing % exceeds this
DROP_COLUMN_THRESHOLD = 60.0

# Threshold: if a categorical has many unique values, fill with "missing"
HIGH_CARDINALITY_THRESHOLD = 20


# ─────────────────────────────────────────────
#  STEP 1 — REMOVE DUPLICATES
# ─────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Identifies and removes completely duplicated rows in the dataset.

    Args:
        df (pd.DataFrame): The input pandas DataFrame.

    Returns:
        Tuple[pd.DataFrame, str]: A tuple containing the deduplicated DataFrame and a descriptive string of the action taken.
    """

    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    after = len(df)
    removed = before - after

    detail = (
        f"removed {removed} duplicate rows ({before} → {after} rows)"
        if removed > 0
        else "no duplicate rows found"
    )
    return df, detail


# ─────────────────────────────────────────────
#  STEP 2 — HANDLE MISSING VALUES
# ─────────────────────────────────────────────

def handle_missing(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
) -> Tuple[pd.DataFrame, str]:
    """
    Imputes or drops missing values dynamically based on Module 1's schema and column semantic meaning.

    Strategy per column:
        - Drop column  → missing > 60%
        - Median       → numeric + skewed meaning keyword
        - Mean         → numeric + normal meaning keyword
        - Mode         → categorical, low cardinality
        - "missing"    → categorical, high cardinality
        - Forward fill → datetime
        - Drop rows    → anything left after column strategies

    Args:
        df (pd.DataFrame): The input DataFrame, ideally deduplicated beforehand.
        module1_output (Dict[str, Any]): The complete context dictionary from Module 1.

    Returns:
        Tuple[pd.DataFrame, str]: A tuple containing the DataFrame with missing values handled and a detailed summary of actions.
    """

    schema         = module1_output.get("data_schema", {})
    data_quality   = module1_output.get("data_quality", {})
    col_meanings   = module1_output.get("column_meanings", {})
    missing_pct    = data_quality.get("missing_percent", {})

    numeric_cols     = schema.get("numeric", [])
    categorical_cols = schema.get("categorical", [])
    datetime_cols    = schema.get("datetime", [])

    actions = []        # human-readable log of what happened
    cols_to_drop = []   # columns we decide to drop entirely

    # ── Pass 1: Drop columns with too much missing data ──
    for col in df.columns:
        if col not in df.columns:
            continue
        pct = missing_pct.get(col, 0.0)
        if pct is None:
            pct = 0.0
        # Also compute directly from df in case Module 1 used a sample
        actual_pct = df[col].isnull().mean() * 100

        # Use the worse of the two estimates
        effective_pct = max(float(pct), actual_pct)

        if effective_pct >= DROP_COLUMN_THRESHOLD:
            cols_to_drop.append(col)
            actions.append(f"dropped '{col}' ({effective_pct:.1f}% missing)")

    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # ── Pass 2: Impute remaining missing values ──
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue  # no missing → skip

        meaning = col_meanings.get(col, "").lower()

        if col in numeric_cols and pd.api.types.is_numeric_dtype(df[col]):
            strategy = _choose_numeric_strategy(col, meaning)
            if strategy == "median":
                fill_val = df[col].median()
                df[col] = df[col].fillna(fill_val)
                actions.append(
                    f"imputed '{col}' with median={round(fill_val, 2)} (numeric/skewed)"
                )
            else:
                fill_val = df[col].mean()
                df[col] = df[col].fillna(fill_val)
                actions.append(
                    f"imputed '{col}' with mean={round(fill_val, 2)} (numeric/normal)"
                )
# CASE 2 — CATEGORICAL
        elif col in categorical_cols:
            n_unique = df[col].nunique()
            if n_unique <= HIGH_CARDINALITY_THRESHOLD:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    actions.append(
                        f"imputed '{col}' with mode='{mode_val[0]}' (categorical)"
                    )
            else:
                df[col] = df[col].fillna("missing")
                actions.append(
                    f"imputed '{col}' with 'missing' (high-cardinality categorical)"
                )
# CASE 3 — DATETIME
        elif col in datetime_cols:
            df[col] = df[col].fillna(method="ffill")
            remaining = df[col].isnull().sum()
            if remaining > 0:
                df[col] = df[col].fillna(method="bfill")
            actions.append(f"imputed '{col}' with forward/backward fill (datetime)")
            
# CASE 4 — UNKNOWN
        else:
            # Unknown type — try numeric first, then mode, then "missing"
            if pd.api.types.is_numeric_dtype(df[col]):
                fill_val = df[col].median()
                df[col] = df[col].fillna(fill_val)
                actions.append(f"imputed '{col}' with median (unknown/numeric)")
            else:
                df[col] = df[col].fillna("missing")
                actions.append(f"imputed '{col}' with 'missing' (unknown type)")

    # ── Pass 3: Drop any remaining rows that still have nulls ──
    remaining_nulls = df.isnull().sum().sum()
    if remaining_nulls > 0:
        before_rows = len(df)
        df = df.dropna().reset_index(drop=True)
        dropped_rows = before_rows - len(df)
        actions.append(
            f"dropped {dropped_rows} rows with remaining null values"
        )

    # Build summary detail message
    if actions:
        detail = f"{len(actions)} cleaning actions: " + "; ".join(actions)
    else:
        detail = "no missing values found — nothing to clean"

    return df, detail


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _choose_numeric_strategy(col_name: str, meaning: str) -> str:
    """
    Determines the appropriate imputation strategy (median or mean) for a numeric column.

    Uses the column's semantic meaning from Module 1 to guess the distribution shape.
    Variables prone to skewness (like age, salary, or fare) default to median imputation.

    Args:
        col_name (str): The name of the numeric column.
        meaning (str): The natural language semantic meaning of the column.

    Returns:
        str: The imputation strategy to use, either "median" or "mean".
    """
    text_to_check = f"{col_name.lower()} {meaning}"
    for keyword in SKEWED_MEANING_KEYWORDS:
        if keyword in text_to_check:
            return "median"
    return "median"   # default to median — always safer than mean


def get_missing_summary(df: pd.DataFrame) -> dict:
    """
    Calculates a summary of missing values for all columns containing nulls.

    This summary is often used by the agent planner to decide if the missing value handler tool needs to be invoked.

    Args:
        df (pd.DataFrame): The DataFrame to evaluate.

    Returns:
        dict: A dictionary mapping column names to integer counts of missing values.
    """
    missing = df.isnull().sum()
    return {
        col: int(count)
        for col, count in missing.items()
        if count > 0
    }
