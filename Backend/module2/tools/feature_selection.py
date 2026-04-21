
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple

from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder


# ─────────────────────────────────────────────────────────────────────────────
# Thresholds — conservative defaults (better to keep than lose signal)
# ─────────────────────────────────────────────────────────────────────────────
VARIANCE_THRESHOLD    = 0.01   # drop if std/range < 1% of column range
CORRELATION_THRESHOLD = 0.95   # drop one of a pair if |corr| > this
MI_BOTTOM_PERCENTILE  = 10     # drop bottom 10% by mutual information score


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def select_features(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
    target_col: str = None,
    variance_threshold: float = VARIANCE_THRESHOLD,
    corr_threshold: float     = CORRELATION_THRESHOLD,
    mi_bottom_pct: float      = MI_BOTTOM_PERCENTILE,
) -> Tuple[pd.DataFrame, List[str], Dict[str, str], str]:
    """
    Parameters
    ----------
    df                  : fully preprocessed DataFrame (post encoding + scaling)
    module1_output      : full dict from Module 1
    target_col          : target column — never dropped, used for MI scoring
    variance_threshold  : fraction of range below which a column is dropped
    corr_threshold      : correlation above which one of a pair is dropped
    mi_bottom_pct       : bottom percentile of MI scores to drop

    Returns
    -------
    df_out          : DataFrame with selected columns only
    kept_cols       : list of surviving column names
    dropped_report  : {col: reason} dict — full transparency
    notes           : summary string for memory.py
    """
    schema          = module1_output.get("data_schema", {})
    column_meanings = module1_output.get("column_meanings", {})

    dropped_report: Dict[str, str] = {}

    # ── Step 0: Always-drop columns ──────────────────────────────────────────
    always_drop = _get_always_drop(schema, target_col)
    for col in always_drop:
        if col in df.columns:
            dropped_report[col] = "always-drop: ID or raw datetime column"

    working_cols = [c for c in df.columns if c not in always_drop]
    df_work = df[working_cols].copy()

    # Columns the selection stages must never remove
    protected = _build_protected_set(schema, column_meanings, target_col)

    # ── Stage 1: Variance filter ─────────────────────────────────────────────
    low_var_cols = _variance_filter(df_work, protected, variance_threshold)
    for col in low_var_cols:
        dropped_report[col] = (
            f"stage1-variance: near-zero variance (threshold={variance_threshold})"
        )
    df_work.drop(columns=low_var_cols, inplace=True)

    # ── Stage 2: Correlation filter ──────────────────────────────────────────
    corr_drop = _correlation_filter(df_work, protected, corr_threshold)
    for col, partner in corr_drop.items():
        dropped_report[col] = (
            f"stage2-correlation: corr>{corr_threshold:.2f} with '{partner}'"
        )
    df_work.drop(columns=list(corr_drop.keys()), inplace=True)

    # ── Stage 3: Mutual information filter ───────────────────────────────────
    if target_col and target_col in df_work.columns:
        mi_drop = _mi_filter(df_work, target_col, protected, mi_bottom_pct)
        for col in mi_drop:
            dropped_report[col] = (
                f"stage3-mutual-info: bottom {mi_bottom_pct}% MI score with target"
            )
        df_work.drop(columns=mi_drop, inplace=True)

    # ── Final output ─────────────────────────────────────────────────────────
    kept_cols = list(df_work.columns)
    df_out    = df_work.copy()

    # ── Build notes ──────────────────────────────────────────────────────────
    notes = _build_notes(len(df.columns), kept_cols, dropped_report)

    return df_out, kept_cols, dropped_report, notes


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Variance filter
# ─────────────────────────────────────────────────────────────────────────────

def _variance_filter(
    df: pd.DataFrame,
    protected: set,
    threshold: float,
) -> List[str]:
    """Return numeric columns with near-zero variance."""
    drop = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if col in protected:
            continue
        s = df[col].dropna()
        if len(s) == 0:
            drop.append(col)
            continue
        col_range = float(s.max() - s.min())
        col_std   = float(s.std())
        col_mean = abs(float(s.mean()))
        if col_range == 0:
            drop.append(col)
        elif col_range > 0 and (col_std / col_range) < threshold:
            drop.append(col)
        elif col_mean > 0 and (col_std / col_mean) < threshold:
            drop.append(col)
    return drop


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Correlation filter
# ─────────────────────────────────────────────────────────────────────────────

def _correlation_filter(
    df: pd.DataFrame,
    protected: set,
    threshold: float,
) -> Dict[str, str]:
    """
    Find correlated pairs. Keep higher-variance column, drop the other.
    Returns {col_to_drop: correlated_partner}.
    """
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return {}

    corr_matrix     = num_df.corr().abs()
    drop_map        : Dict[str, str] = {}
    already_dropped : set            = set()

    cols = list(corr_matrix.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            c1, c2 = cols[i], cols[j]
            if c1 in already_dropped or c2 in already_dropped:
                continue
            if corr_matrix.loc[c1, c2] <= threshold:
                continue

            # Both protected → skip
            if c1 in protected and c2 in protected:
                continue

            var1 = float(df[c1].var())
            var2 = float(df[c2].var())

            if c1 in protected:
                to_drop, partner = c2, c1
            elif c2 in protected:
                to_drop, partner = c1, c2
            else:
                to_drop, partner = (c2, c1) if var1 >= var2 else (c1, c2)

            drop_map[to_drop] = partner
            already_dropped.add(to_drop)

    return drop_map


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — Mutual information filter
# ─────────────────────────────────────────────────────────────────────────────

def _mi_filter(
    df: pd.DataFrame,
    target_col: str,
    protected: set,
    bottom_pct: float,
) -> List[str]:
    """
    Score columns by mutual information with target.
    Drop bottom `bottom_pct` percent. Skip if fewer than 5 features.
    """
    feature_cols = [
        c for c in df.columns
        if c != target_col
        and c not in protected
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    if len(feature_cols) <= 5:
        return []

    # Fill NaN with median for MI calculation only
    X = df[feature_cols].copy()
    for col in X.columns:
        X[col] = X[col].fillna(X[col].median())

    y = df[target_col].fillna(df[target_col].median())

    try:
        n_unique = int(df[target_col].nunique())
        if n_unique <= 20:
            y_enc = LabelEncoder().fit_transform(y.astype(str))
            mi_scores = mutual_info_classif(X, y_enc, random_state=42)
        else:
            mi_scores = mutual_info_regression(X, y, random_state=42)
    except Exception:
        return []   # safe fallback — never drop if MI fails

    mi_series = pd.Series(mi_scores, index=feature_cols)

    # If everything scores 0 (no signal), don't drop anything
    if float(mi_series.max()) == 0:
        return []

    cutoff    = float(np.percentile(mi_scores, bottom_pct))
    drop_cols = list(mi_series[mi_series < cutoff].index)
    return drop_cols


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_always_drop(schema: Dict, target_col: str) -> set:
    """Columns dropped before any selection logic runs."""
    always = set()
    for col in schema.get("id", []):
        always.add(col)
    for col in schema.get("datetime", []):
        always.add(col)
    always.discard(target_col)   # never drop target even if in id/datetime
    return always


def _build_protected_set(
    schema: Dict,
    column_meanings: Dict,
    target_col: str,
) -> set:
    """Columns the selection stages must never drop."""
    protected = set()
    if target_col:
        protected.add(target_col)
    # Any column with a documented meaning is considered important
    for col, meaning in column_meanings.items():
        if meaning and len(str(meaning).strip()) > 5:
            protected.add(col)
    return protected


def _build_notes(
    total_start: int,
    kept_cols: List[str],
    dropped_report: Dict[str, str],
) -> str:
    lines = [
        f"Feature selection: {total_start} columns in → "
        f"{len(kept_cols)} kept, {len(dropped_report)} dropped",
        "",
    ]
    if dropped_report:
        lines.append("Dropped:")
        for col, reason in dropped_report.items():
            lines.append(f"  • {col}: {reason}")
        lines.append("")
    lines.append("Kept: " + ", ".join(kept_cols))
    return "\n".join(lines)
