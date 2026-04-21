"""
tools/scaling.py
----------------
Smart numeric scaling tool for Module 2.

Reads Module 1 output to make intelligent scaling decisions:
  - schema["numeric"]    → columns eligible for scaling
  - column_meanings      → skip ID-like, flag, binary columns
  - data_quality         → columns with high outlier warnings → RobustScaler
  - schema["boolean"]    → never scale boolean/flag columns

Scaling strategy per column:
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Already binary (0/1 only)       → skip  (already scaled)           │
  │  High outlier flag from Module 1  → RobustScaler  (median/IQR)      │
  │  Bounded range (0–1 or known max) → MinMaxScaler  (0 to 1)          │
  │  Normal / near-normal             → StandardScaler (z-score)        │
  │  Default fallback                 → StandardScaler                  │
  └──────────────────────────────────────────────────────────────────────┘

Returns:
  df_out       : DataFrame with scaled numeric columns (in-place replacement)
  scaler_map   : {col: fitted scaler object} — save and reuse on test data
  scaling_log  : [(col, strategy, detail), ...]
  notes        : human-readable summary string for memory.py
"""

import re
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple

from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler


# ─────────────────────────────────────────────────────────────────────────────
# Patterns for columns that must never be scaled
# ─────────────────────────────────────────────────────────────────────────────
_ID_PATTERN = re.compile(
    r"\b(id|identifier|key|code|index|serial|uuid|hash)\b", re.IGNORECASE
)
_FLAG_PATTERN = re.compile(
    r"\b(flag|indicator|dummy|is_|has_|was_|did_|active|bool)\b", re.IGNORECASE
)

# Columns whose values are already bounded [0, 1] — MinMax is fine but
# StandardScaler would shrink them unnecessarily
_RATE_PATTERN = re.compile(
    r"\b(rate|ratio|percent|pct|proportion|probability|prob|score|share)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def scale_features(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
    target_col: str = None,
) -> Tuple[pd.DataFrame, Dict[str, Any], List[Tuple[str, str, str]], str]:
    """
    Parameters
    ----------
    df              : DataFrame after encoding step
    module1_output  : full dict from Module 1
    target_col      : target column name — never scaled

    Returns
    -------
    df_out          : DataFrame with scaled numeric columns
    scaler_map      : {col: fitted sklearn scaler} — reuse for test data
    scaling_log     : [(col, strategy, detail), ...]
    notes           : summary string for memory.py
    """
    schema          = module1_output.get("data_schema", {})
    column_meanings = module1_output.get("column_meanings", {})
    data_quality    = module1_output.get("data_quality", {})

    # Columns flagged as having outliers by Module 1
    outlier_warnings = _extract_outlier_cols(data_quality)

    # Build the set of all numeric-like columns in the current df
    # (includes engineered features like Fare_log, family_size, etc.)
    schema_numeric = set(schema.get("numeric", []))
    boolean_cols   = set(schema.get("boolean", []))

    # All numeric dtype columns present in df
    df_numeric_cols = set(df.select_dtypes(include=[np.number]).columns)

    # Candidate columns = schema numeric ∪ engineered numeric cols, minus booleans
    candidate_cols = (schema_numeric | df_numeric_cols) - boolean_cols

    # Build protection set
    protected = _build_protected_set(schema, column_meanings, target_col)

    df_out      = df.copy()
    scaler_map  : Dict[str, Any]                    = {}
    scaling_log : List[Tuple[str, str, str]]        = []
    skipped_log : List[str]                         = []

    for col in sorted(candidate_cols):
        if col not in df_out.columns:
            continue
        if col in protected:
            skipped_log.append(f"{col} (protected)")
            continue
        if not pd.api.types.is_numeric_dtype(df_out[col]):
            continue

        series = df_out[col].dropna()
        if len(series) == 0:
            skipped_log.append(f"{col} (all null)")
            continue

        # Skip already-binary columns
        if _is_binary_column(df_out[col]):
            skipped_log.append(f"{col} (already binary 0/1)")
            continue

        meaning   = column_meanings.get(col, "")
        strategy  = _choose_strategy(col, meaning, df_out[col], outlier_warnings)

        scaler    = _get_scaler(strategy)
        values    = df_out[col].values.reshape(-1, 1)

        # Handle NaNs: fit on non-null, transform all
        not_null  = ~df_out[col].isna()
        scaler.fit(df_out.loc[not_null, col].values.reshape(-1, 1))
        df_out.loc[not_null, col] = scaler.transform(
            df_out.loc[not_null, col].values.reshape(-1, 1)
        ).flatten()

        scaler_map[col]  = scaler
        detail = _describe_scaler(scaler, df_out[col])
        scaling_log.append((col, strategy, detail))

    # ── Build notes ──────────────────────────────────────────────────────────
    scaled_lines  = [f"  • {col} [{strat}]: {detail}"
                     for col, strat, detail in scaling_log]
    skipped_lines = [f"  • {s}" for s in skipped_log]

    notes_parts = []
    if scaled_lines:
        notes_parts.append(f"Scaled {len(scaling_log)} columns:\n" + "\n".join(scaled_lines))
    if skipped_lines:
        notes_parts.append(f"Skipped {len(skipped_log)} columns:\n" + "\n".join(skipped_lines))
    notes = "\n\n".join(notes_parts) if notes_parts else "No numeric columns to scale."

    return df_out, scaler_map, scaling_log, notes


# ─────────────────────────────────────────────────────────────────────────────
# Strategy selection
# ─────────────────────────────────────────────────────────────────────────────

def _choose_strategy(
    col: str,
    meaning: str,
    series: pd.Series,
    outlier_warnings: set,
) -> str:
    """Pick the best scaler strategy for this column."""
    col_text = (col + " " + meaning).lower()

    # Columns Module 1 flagged as having outliers → RobustScaler
    if col in outlier_warnings:
        return "robust"

    # Rate / proportion columns with values already in [0, 1]
    if _RATE_PATTERN.search(col_text):
        mn, mx = series.dropna().min(), series.dropna().max()
        if mn >= 0 and mx <= 1:
            return "minmax"

    # Columns with very heavy skew → RobustScaler handles the tail better
    try:
        skewness = abs(float(series.dropna().skew()))
    except Exception:
        skewness = 0.0

    if skewness > 2.0:
        return "robust"

    # Columns with known hard lower bound at 0 and finite range → MinMax
    if series.dropna().min() >= 0:
        cv = series.dropna().std() / (series.dropna().mean() + 1e-9)
        if cv < 1.0:        # low coefficient of variation → well-behaved range
            return "minmax"

    # Default: StandardScaler
    return "standard"


def _get_scaler(strategy: str):
    """Return a fresh sklearn scaler for the given strategy."""
    if strategy == "robust":
        return RobustScaler()
    elif strategy == "minmax":
        return MinMaxScaler()
    else:
        return StandardScaler()


def _describe_scaler(scaler, series: pd.Series) -> str:
    """Human-readable description of what the scaler did."""
    s = series.dropna()
    if isinstance(scaler, StandardScaler):
        return (f"z-score: mean={float(s.mean()):.2f}, "
                f"std={float(s.std()):.2f} → range [{float(s.min()):.2f}, {float(s.max()):.2f}]")
    elif isinstance(scaler, MinMaxScaler):
        return f"minmax: range [{float(s.min()):.3f}, {float(s.max()):.3f}]"
    elif isinstance(scaler, RobustScaler):
        return (f"robust: median={float(s.median()):.2f}, "
                f"IQR={float(s.quantile(0.75) - s.quantile(0.25)):.2f}")
    return "scaled"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_binary_column(series: pd.Series) -> bool:
    """True if column contains only 0 and 1 (and nulls)."""
    unique_vals = set(series.dropna().unique())
    return unique_vals.issubset({0, 1, 0.0, 1.0})


def _extract_outlier_cols(data_quality: Dict) -> set:
    """
    Extract column names that Module 1 flagged as having outliers.
    Module 1 stores these in data_quality["warnings"] as strings like
    'Column Age has X outliers detected via IQR'.
    """
    outlier_cols = set()
    warnings = data_quality.get("warnings", [])
    if isinstance(warnings, list):
        for w in warnings:
            w_lower = str(w).lower()
            if "outlier" in w_lower:
                # Extract column name — pattern: "Column <name> has"
                m = re.search(r"column\s+['\"]?(\w+)['\"]?\s+has", w_lower)
                if m:
                    outlier_cols.add(m.group(1))
    # Also check outlier_summary if present
    outlier_summary = data_quality.get("outlier_summary", {})
    if isinstance(outlier_summary, dict):
        for col, info in outlier_summary.items():
            if isinstance(info, dict) and info.get("count", 0) > 0:
                outlier_cols.add(col)
            elif isinstance(info, (int, float)) and info > 0:
                outlier_cols.add(col)
    return outlier_cols


def _build_protected_set(
    schema: Dict,
    column_meanings: Dict,
    target_col: str,
) -> set:
    """Columns that must never be scaled."""
    protected = set()

    if target_col:
        protected.add(target_col)

    # ID columns from schema
    for col in schema.get("id", []):
        protected.add(col)

    # Datetime columns
    for col in schema.get("datetime", []):
        protected.add(col)

    # Column name or meaning looks like an ID or flag
    all_cols = (
        schema.get("numeric", []) +
        schema.get("categorical", []) +
        schema.get("boolean", [])
    )
    for col in all_cols:
        meaning = column_meanings.get(col, "")
        col_text = col + " " + meaning
        if _ID_PATTERN.search(col_text) or _FLAG_PATTERN.search(col_text):
            protected.add(col)

    return protected


# ─────────────────────────────────────────────────────────────────────────────
# Inference helper — apply saved scalers to new data
# ─────────────────────────────────────────────────────────────────────────────

def apply_saved_scaling(
    df: pd.DataFrame,
    scaler_map: Dict[str, Any],
) -> pd.DataFrame:
    """
    Re-apply fitted scalers to new data (e.g. test / inference set).
    Call this instead of scale_features() at inference time.

    Parameters
    ----------
    df          : new DataFrame (same columns as training data)
    scaler_map  : dict returned by scale_features() during training

    Returns
    -------
    df_out      : DataFrame with same scaling applied
    """
    df_out = df.copy()
    for col, scaler in scaler_map.items():
        if col not in df_out.columns:
            continue
        not_null = ~df_out[col].isna()
        if not_null.sum() == 0:
            continue
        df_out.loc[not_null, col] = scaler.transform(
            df_out.loc[not_null, col].values.reshape(-1, 1)
        ).flatten()
    return df_out
