"""
Universal feature engineering tool for Module 2.
"""

import re
import math
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple


# ─────────────────────────────────────────────
# Keyword groups used for combination detection
# ─────────────────────────────────────────────
_FAMILY_KEYWORDS   = {"sibling", "spouse", "sibsp", "parent", "child", "parch", "family"}
_PRICE_KEYWORDS    = {"price", "fare", "cost", "amount", "revenue", "salary", "wage", "income"}
_AGE_KEYWORDS      = {"age", "years", "tenure", "experience"}
_COUNT_KEYWORDS    = {"count", "num", "number", "qty", "quantity", "total"}
_RATE_KEYWORDS     = {"rate", "ratio", "percent", "pct", "proportion", "share"}

# Columns whose meaning suggests they are IDs — never engineer these
_ID_PATTERNS = re.compile(
    r"\b(id|identifier|key|code|index|serial|uuid|hash)\b", re.IGNORECASE
)


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def engineer_features(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
    target_col: str = None,
) -> Tuple[pd.DataFrame, List[Tuple[str, str]], str]:
    """
    Parameters
    ----------
    df              : cleaned DataFrame (after cleaning + outlier steps)
    module1_output  : full dict from Module 1
    target_col      : name of the target column to protect (never engineered)

    Returns
    -------
    df_out          : DataFrame with new columns appended
    features_added  : [(col_name, description), ...]
    notes           : summary string for memory.py
    """
    schema             = module1_output.get("data_schema", {})
    column_meanings    = module1_output.get("column_meanings", {})
    suggested_analyses = module1_output.get("suggested_analyses", [])

    numeric_cols   = [c for c in schema.get("numeric",   []) if c in df.columns]
    datetime_cols  = [c for c in schema.get("datetime",  []) if c in df.columns]
    categorical_cols = [c for c in schema.get("categorical", []) if c in df.columns]

    # Build a set of columns to never touch
    protected = _build_protected_set(df, schema, column_meanings, target_col)

    df_out = df.copy()
    features_added: List[Tuple[str, str]] = []

    # ── 1. Datetime extraction ──────────────────────────────────────────────
    for col in datetime_cols:
        if col in protected:
            continue
        new_feats = _extract_datetime_parts(df_out, col)
        for new_col, desc in new_feats:
            df_out[new_col] = _extract_datetime_part_values(df_out[col], new_col.split("_")[-1])
            features_added.append((new_col, desc))

    # ── 2. Log transform skewed numerics ────────────────────────────────────
    for col in numeric_cols:
        if col in protected:
            continue
        if _is_skewed(df_out[col]) and _is_positive_safe(df_out[col]):
            new_col = f"{col}_log"
            df_out[new_col] = np.log1p(df_out[col])
            features_added.append((new_col, f"log1p transform of skewed column '{col}'"))

    # ── 3. Age / numeric binning ─────────────────────────────────────────────
    for col in numeric_cols:
        if col in protected:
            continue
        meaning = column_meanings.get(col, "").lower()
        col_lower = col.lower()
        if any(kw in col_lower or kw in meaning for kw in _AGE_KEYWORDS):
            new_col = f"{col}_group"
            df_out[new_col] = _bin_age(df_out[col])
            features_added.append((new_col, f"age/tenure group bins for '{col}'"))

    # ── 4. Family / combination features ────────────────────────────────────
    combo_feats = _detect_combination_features(df_out, numeric_cols, column_meanings, protected)
    for new_col, expr, desc in combo_feats:
        try:
            df_out[new_col] = df_out.eval(expr)
            features_added.append((new_col, desc))
        except Exception:
            pass  # safe skip if eval fails

    # ── 5. Ratio features ────────────────────────────────────────────────────
    ratio_feats = _detect_ratio_features(df_out, numeric_cols, column_meanings, protected)
    for new_col, num_col, den_col, desc in ratio_feats:
        denominator = df_out[den_col].replace(0, np.nan)
        df_out[new_col] = df_out[num_col] / denominator
        features_added.append((new_col, desc))

    # ── 6. Low-cardinality categorical interaction ───────────────────────────
    low_card_cats = [
        c for c in categorical_cols
        if c not in protected and df_out[c].nunique() <= 5
    ]
    if len(low_card_cats) >= 2:
        c1, c2 = low_card_cats[0], low_card_cats[1]
        new_col = f"{c1}_x_{c2}"
        df_out[new_col] = df_out[c1].astype(str) + "_" + df_out[c2].astype(str)
        features_added.append((new_col, f"interaction between '{c1}' and '{c2}'"))

    # ── 7. Honour suggested_analyses hints ──────────────────────────────────
    hint_feats = _apply_suggested_hints(df_out, suggested_analyses, numeric_cols, protected)
    for new_col, desc in hint_feats:
        features_added.append((new_col, desc))

    # ── Build notes ──────────────────────────────────────────────────────────
    if features_added:
        lines = [f"  • {name}: {desc}" for name, desc in features_added]
        notes = f"Feature engineering added {len(features_added)} columns:\n" + "\n".join(lines)
    else:
        notes = "No feature engineering applied — dataset did not meet any criteria."

    return df_out, features_added, notes


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_protected_set(
    df: pd.DataFrame,
    schema: Dict,
    column_meanings: Dict,
    target_col: str,
) -> set:
    """Columns that must never be engineered."""
    protected = set()
    if target_col:
        protected.add(target_col)

    # ID columns from schema
    for col in schema.get("id", []):
        protected.add(col)

    # Columns whose name or meaning looks like an ID
    for col in df.columns:
        meaning = column_meanings.get(col, "")
        if _ID_PATTERNS.search(col) or _ID_PATTERNS.search(meaning):
            protected.add(col)

    return protected


def _is_skewed(series: pd.Series, threshold: float = 1.0) -> bool:
    """True if absolute skewness exceeds threshold."""
    s = series.dropna()
    if len(s) < 10:
        return False
    try:
        return abs(float(s.skew())) > threshold
    except Exception:
        return False


def _is_positive_safe(series: pd.Series) -> bool:
    """True if all non-null values are >= 0 (safe for log1p)."""
    s = series.dropna()
    return len(s) > 0 and float(s.min()) >= 0


def _bin_age(series: pd.Series) -> pd.Series:
    """Bin a numeric series into meaningful age/tenure groups."""
    mn, mx = series.min(), series.max()
    if mx <= 1:           # proportion / rate — skip
        return pd.Series([np.nan] * len(series), index=series.index)
    if mx <= 20:
        bins   = [0, 5, 10, 15, 20, 999]
        labels = ["0-5", "6-10", "11-15", "16-20", "20+"]
    elif mx <= 100:
        bins   = [0, 18, 35, 50, 65, 999]
        labels = ["child", "young_adult", "adult", "middle_age", "senior"]
    else:
        # tenure / experience in years
        q1, q2, q3 = series.quantile([0.25, 0.5, 0.75])
        bins   = [-np.inf, q1, q2, q3, np.inf]
        labels = ["low", "medium", "high", "very_high"]
    return pd.cut(series, bins=bins, labels=labels, right=False)


def _extract_datetime_parts(df: pd.DataFrame, col: str) -> List[Tuple[str, str]]:
    """Return list of (new_col_name, description) for datetime parts to extract."""
    parts = []
    s = pd.to_datetime(df[col], errors="coerce")
    if s.dt.year.nunique() > 1:
        parts.append((f"{col}_year",    f"year extracted from '{col}'"))
    if s.dt.month.nunique() > 1:
        parts.append((f"{col}_month",   f"month extracted from '{col}'"))
    if s.dt.day.nunique() > 1:
        parts.append((f"{col}_day",     f"day of month extracted from '{col}'"))
    if s.dt.dayofweek.nunique() > 1:
        parts.append((f"{col}_weekday", f"weekday (0=Mon) extracted from '{col}'"))
    if s.dt.hour.nunique() > 1:
        parts.append((f"{col}_hour",    f"hour extracted from '{col}'"))
    return parts


def _extract_datetime_part_values(series: pd.Series, part: str) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce")
    mapping = {
        "year":    s.dt.year,
        "month":   s.dt.month,
        "day":     s.dt.day,
        "weekday": s.dt.dayofweek,
        "hour":    s.dt.hour,
    }
    return mapping.get(part, pd.Series([np.nan] * len(series)))


def _detect_combination_features(
    df: pd.DataFrame,
    numeric_cols: List[str],
    column_meanings: Dict,
    protected: set,
) -> List[Tuple[str, str, str]]:
    """
    Detect columns that should be summed together.
    Returns list of (new_col, eval_expr, description).
    """
    results = []
    cols_lower = {
        c: (c.lower() + " " + column_meanings.get(c, "").lower())
        for c in numeric_cols if c not in protected
    }

    # Family size: SibSp + Parch
    family_cols = [c for c, txt in cols_lower.items() if any(kw in txt for kw in _FAMILY_KEYWORDS)]
    if len(family_cols) >= 2:
        expr = " + ".join(family_cols) + " + 1"
        results.append(("family_size", expr, f"combined family size from {family_cols}"))

    # Count / quantity sums
    count_cols = [c for c, txt in cols_lower.items() if any(kw in txt for kw in _COUNT_KEYWORDS)]
    if len(count_cols) >= 2:
        expr = " + ".join(count_cols)
        results.append(("total_count", expr, f"total count from {count_cols}"))

    return results


def _detect_ratio_features(
    df: pd.DataFrame,
    numeric_cols: List[str],
    column_meanings: Dict,
    protected: set,
) -> List[Tuple[str, str, str, str]]:
    """
    Detect meaningful ratio pairs.
    Returns list of (new_col, numerator_col, denominator_col, description).
    """
    results = []
    cols_lower = {
        c: (c.lower() + " " + column_meanings.get(c, "").lower())
        for c in numeric_cols if c not in protected
    }

    price_cols = [c for c, txt in cols_lower.items() if any(kw in txt for kw in _PRICE_KEYWORDS)]
    count_cols = [c for c, txt in cols_lower.items() if any(kw in txt for kw in _COUNT_KEYWORDS)]

    # price-per-count (e.g. fare per person)
    if price_cols and count_cols:
        num, den = price_cols[0], count_cols[0]
        if num != den:
            results.append((
                f"{num}_per_{den}",
                num, den,
                f"ratio of '{num}' divided by '{den}'"
            ))

    return results


def _apply_suggested_hints(
    df: pd.DataFrame,
    suggested_analyses: List[str],
    numeric_cols: List[str],
    protected: set,
) -> List[Tuple[str, str]]:
    """
    Read Module 1's suggested_analyses list for feature hints.
    Returns (new_col, desc) for any features we can act on.
    """
    results = []
    suggestions_text = " ".join(str(s) for s in suggested_analyses).lower()

    # If Module 1 suggested log transform and we haven't done it yet
    if "log" in suggestions_text:
        for col in numeric_cols:
            if col in protected:
                continue
            new_col = f"{col}_log_hint"
            if new_col not in df.columns and _is_positive_safe(df[col]):
                # Only add if not already log-transformed
                base_log = f"{col}_log"
                if base_log not in df.columns and _is_skewed(df[col], threshold=0.5):
                    df[base_log] = np.log1p(df[col])
                    results.append((base_log, f"log transform suggested by Module 1 analysis"))
                    break  # one is enough to honour the hint

    # If Module 1 suggested interaction or cross features
    if "interaction" in suggestions_text or "cross" in suggestions_text:
        safe_nums = [c for c in numeric_cols if c not in protected][:2]
        if len(safe_nums) == 2:
            c1, c2 = safe_nums
            new_col = f"{c1}_times_{c2}"
            if new_col not in df.columns:
                df[new_col] = df[c1] * df[c2]
                results.append((new_col, f"multiplicative interaction suggested by Module 1"))

    return results
