"""
tools/encoding.py
-----------------
Smart categorical encoding tool for Module 2.

Reads Module 1 output to make smart encoding decisions:
  - schema["categorical"]  → columns to encode
  - schema["boolean"]      → simple True/False → 1/0 map
  - column_meanings        → detect high-cardinality (cities, names) → freq encoding
  - target_col             → NEVER encode the target column

Encoding strategy per column:
  ┌─────────────────────────────────────────────────────────────┐
  │  boolean column             → binary map  (True=1, False=0) │
  │  2 unique values            → binary map  (0 / 1)           │
  │  3–10 unique values         → one-hot     (drop first)      │
  │  11–50 unique values        → ordinal     (frequency order) │
  │  > 50 unique values         → frequency   (replace w/ count)│
  └─────────────────────────────────────────────────────────────┘

Returns:
  df_out          : DataFrame with encoded columns (originals dropped)
  encoder_map     : dict of {col: fitted encoder / mapping} for reuse
  encoding_log    : list of (col, strategy, detail) for memory.py
  notes           : human-readable summary string
"""

import re
import pickle
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────────────────────────────
BINARY_MAX      = 2
ONEHOT_MAX      = 10
ORDINAL_MAX     = 50
# Above ORDINAL_MAX → frequency encoding

# Column name / meaning patterns that hint at high-cardinality free text
_HIGH_CARD_PATTERNS = re.compile(
    r"\b(city|town|state|country|region|zip|postal|address|name|title"
    r"|description|comment|note|text|label|category|product|brand|sku)\b",
    re.IGNORECASE,
)

# Boolean-like string values
_TRUE_VALUES  = {"true", "yes", "1", "t", "y", "on"}
_FALSE_VALUES = {"false", "no", "0", "f", "n", "off"}


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def encode_categoricals(
    df: pd.DataFrame,
    module1_output: Dict[str, Any],
    target_col: str = None,
) -> Tuple[pd.DataFrame, Dict[str, Any], List[Tuple[str, str, str]], str]:
    """
    Parameters
    ----------
    df              : DataFrame after cleaning + outlier + feature steps
    module1_output  : full dict from Module 1
    target_col      : target column name — never encoded

    Returns
    -------
    df_out          : DataFrame with encoded columns
    encoder_map     : {col_name: mapping/dict} — save this to re-apply on new data
    encoding_log    : [(col, strategy, detail), ...]
    notes           : summary string for memory.py
    """
    schema          = module1_output.get("data_schema", {})
    column_meanings = module1_output.get("column_meanings", {})

    categorical_cols = [c for c in schema.get("categorical", []) if c in df.columns]
    boolean_cols     = [c for c in schema.get("boolean",     []) if c in df.columns]

    # Build protection set
    protected = _build_protected_set(schema, target_col)

    df_out       = df.copy()
    encoder_map  : Dict[str, Any]                    = {}
    encoding_log : List[Tuple[str, str, str]]        = []

    # ── 1. Boolean columns ───────────────────────────────────────────────────
    for col in boolean_cols:
        if col in protected:
            continue
        mapping, detail = _encode_boolean(df_out, col)
        if mapping is not None:
            df_out[col]      = df_out[col].map(mapping).fillna(0).astype(int)
            encoder_map[col] = {"strategy": "boolean", "mapping": mapping}
            encoding_log.append((col, "boolean", detail))

    # ── 2. Categorical columns ───────────────────────────────────────────────
    cols_to_drop = []

    for col in categorical_cols:
        if col in protected:
            continue

        n_unique = df_out[col].nunique(dropna=True)
        meaning  = column_meanings.get(col, "")
        hint_high_card = bool(_HIGH_CARD_PATTERNS.search(col) or
                               _HIGH_CARD_PATTERNS.search(meaning))

        # Choose strategy
        if n_unique <= BINARY_MAX:
            strategy = "binary"
        elif hint_high_card or n_unique > ORDINAL_MAX:
            strategy = "frequency"
        elif n_unique <= ONEHOT_MAX:
            strategy = "onehot"
        else:
            strategy = "ordinal"

        # Apply strategy
        if strategy == "binary":
            mapping, detail = _encode_binary(df_out, col)
            df_out[col]      = df_out[col].map(mapping).fillna(-1).astype(int)
            encoder_map[col] = {"strategy": "binary", "mapping": mapping}
            encoding_log.append((col, "binary", detail))

        elif strategy == "onehot":
            new_cols, mapping, detail = _encode_onehot(df_out, col)
            for new_col, values in new_cols.items():
                df_out[new_col] = values
            cols_to_drop.append(col)
            encoder_map[col] = {"strategy": "onehot", "mapping": mapping}
            encoding_log.append((col, "onehot", detail))

        elif strategy == "ordinal":
            mapping, detail = _encode_ordinal(df_out, col)
            df_out[col]      = df_out[col].map(mapping).fillna(-1).astype(int)
            encoder_map[col] = {"strategy": "ordinal", "mapping": mapping}
            encoding_log.append((col, "ordinal", detail))

        elif strategy == "frequency":
            mapping, detail = _encode_frequency(df_out, col)
            df_out[col]      = df_out[col].map(mapping).fillna(0)
            encoder_map[col] = {"strategy": "frequency", "mapping": mapping}
            encoding_log.append((col, "frequency", detail))

    # Drop original columns that were one-hot expanded
    df_out.drop(columns=cols_to_drop, inplace=True)

    # ── Build notes ──────────────────────────────────────────────────────────
    if encoding_log:
        lines = [f"  • {col} ({strat}): {detail}" for col, strat, detail in encoding_log]
        notes = f"Encoded {len(encoding_log)} columns:\n" + "\n".join(lines)
    else:
        notes = "No categorical encoding needed — no categorical/boolean columns found."

    return df_out, encoder_map, encoding_log, notes


# ─────────────────────────────────────────────────────────────────────────────
# Strategy implementations
# ─────────────────────────────────────────────────────────────────────────────

def _encode_boolean(
    df: pd.DataFrame, col: str
) -> Tuple[Dict, str]:
    """Map boolean-like values to 1/0."""
    unique_vals = df[col].dropna().astype(str).str.lower().unique()
    mapping = {}
    for v in df[col].dropna().unique():
        v_str = str(v).lower()
        if v_str in _TRUE_VALUES:
            mapping[v] = 1
        elif v_str in _FALSE_VALUES:
            mapping[v] = 0
        else:
            # Fallback: True/False dtype
            try:
                mapping[v] = int(bool(v))
            except Exception:
                mapping[v] = -1
    detail = f"mapped {list(mapping.keys())} → {list(mapping.values())}"
    return mapping, detail


def _encode_binary(
    df: pd.DataFrame, col: str
) -> Tuple[Dict, str]:
    """Encode 2-value categorical as 0/1. Safely handles constant columns."""
    vals = sorted(df[col].dropna().unique(), key=str)
    
    if len(vals) == 0:
        return {}, "empty column"
    
    if len(vals) == 1:
        mapping = {vals[0]: 0}
        detail = f"constant value '{vals[0]}' → 0"
        return mapping, detail

    mapping = {vals[0]: 0, vals[1]: 1}
    detail = f"'{vals[0]}'→0, '{vals[1]}'→1"
    return mapping, detail


def _encode_onehot(
    df: pd.DataFrame, col: str
) -> Tuple[Dict[str, pd.Series], Dict, str]:
    """One-hot encode, drop first category to avoid dummy variable trap."""
    dummies  = pd.get_dummies(df[col], prefix=col, drop_first=True, dtype=int)
    new_cols = {c: dummies[c] for c in dummies.columns}
    # Store the category order for reuse
    categories = list(df[col].dropna().unique())
    mapping  = {"categories": categories, "new_columns": list(dummies.columns)}
    detail   = f"{df[col].nunique()} categories → {len(dummies.columns)} dummy cols"
    return new_cols, mapping, detail


def _encode_ordinal(
    df: pd.DataFrame, col: str
) -> Tuple[Dict, str]:
    """Frequency-order ordinal: most frequent = highest integer."""
    freq_order = (
        df[col].value_counts(ascending=True)
              .reset_index()
    )
    # pandas 2.x: columns are [col, 'count']
    if "count" in freq_order.columns:
        freq_order.columns = ["value", "count"]
    else:
        freq_order.columns = ["value", "count"]

    mapping = {row["value"]: rank for rank, row in enumerate(freq_order.to_dict("records"))}
    detail  = f"{len(mapping)} ordinal ranks by frequency"
    return mapping, detail


def _encode_frequency(
    df: pd.DataFrame, col: str
) -> Tuple[Dict, str]:
    """Replace each category with its frequency count in the training data."""
    freq_map = df[col].value_counts().to_dict()
    detail   = f"{len(freq_map)} unique values → replaced by frequency count"
    return freq_map, detail


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_protected_set(schema: Dict, target_col: str) -> set:
    protected = set()
    if target_col:
        protected.add(target_col)
    for col in schema.get("id", []):
        protected.add(col)
    for col in schema.get("numeric", []):
        protected.add(col)
    for col in schema.get("datetime", []):
        protected.add(col)
    return protected


def apply_saved_encoding(
    df: pd.DataFrame,
    encoder_map: Dict[str, Any],
) -> pd.DataFrame:
    """
    Re-apply a saved encoder_map to new data (e.g. test set).
    Call this instead of encode_categoricals() for inference time.
    """
    df_out = df.copy()
    cols_to_drop = []

    for col, enc in encoder_map.items():
        if col not in df_out.columns:
            continue
        strategy = enc["strategy"]
        mapping  = enc["mapping"]

        if strategy in ("boolean", "binary", "ordinal", "frequency"):
            df_out[col] = df_out[col].map(mapping).fillna(-1 if strategy != "frequency" else 0)
            if strategy in ("boolean", "binary"):
                df_out[col] = df_out[col].astype(int)

        elif strategy == "onehot":
            for new_col in mapping["new_columns"]:
                # reconstruct dummy from stored category name
                cat = new_col[len(col) + 1:]   # strip "col_" prefix
                df_out[new_col] = (df_out[col].astype(str) == cat).astype(int)
            cols_to_drop.append(col)

    df_out.drop(columns=cols_to_drop, inplace=True)
    return df_out
