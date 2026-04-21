"""
services/target_detector.py
============================
Identifies the target/label column using Module 1's intelligence.

WHY THIS IS A SERVICE (not a tool)
-----------------------------------
Tools transform data. Services make decisions about data.
This service reads Module 1's output and makes one key decision:
which column is the thing we're trying to predict?

CONNECTION TO MODULE 1
----------------------
module1_output["column_meanings"]
    → "Survival outcome (target variable)" → Survived is the target
    → "Ticket price paid" → not a target
    → "Customer churn indicator" → that's the target

module1_output["data_schema"]["categorical"]
    → target is usually categorical (classification)
    → but can be numeric (regression: price, salary)

module1_output["ai_summary"]
    → contains phrases like "predict survival", "forecast price"
    → we scan this for prediction intent

module1_output["suggested_analyses"]
    → "Survival rate by Sex" → Survival/Survived is the target
    → "Price prediction model" → price is the target

DETECTION STRATEGY (in priority order)
----------------------------------------
1. Explicit keyword in column MEANING  → highest confidence
2. Explicit keyword in column NAME     → high confidence
3. AI summary scan                     → medium confidence
4. Suggested analyses scan             → medium confidence
5. Last column fallback                → low confidence (common ML convention)
"""

import re
from typing import Optional, Tuple

# Keywords that strongly indicate a column is the target
TARGET_MEANING_KEYWORDS = [
    "target", "label", "outcome", "predict", "dependent variable",
    "response variable", "ground truth", "y variable",
]

TARGET_NAME_KEYWORDS = [
    "target", "label", "survived", "survival",
    "churn", "churned",
    "price", "sale_price", "saleprice", "selling_price",
    "sales", "revenue",
    "fraud", "is_fraud",
    "default", "defaulted",
    "diagnosis", "disease",
    "outcome", "result",
    "y", "class", "category",
    "rating", "score",
    "purchased", "converted", "clicked",
]

# Keywords that strongly indicate NOT a target
NON_TARGET_KEYWORDS = [
    "id", "index", "uuid", "key",
    "name", "description", "address", "comment",
    "date", "time", "year", "month",
]


def detect_target(
    df_columns: list,
    module1_output: dict
) -> Tuple[str, str, float]:
    """
    Identify the target column.

    Args:
        df_columns     : List of column names in the DataFrame
        module1_output : Full output dict from Module 1

    Returns:
        (target_column, detection_method, confidence_score)
        target_column    → name of the detected target column
        detection_method → how it was found (for logging)
        confidence_score → 0.0 to 1.0 (how sure we are)
    """
    col_meanings  = module1_output.get("column_meanings", {})
    ai_summary    = module1_output.get("ai_summary", "").lower()
    suggested     = module1_output.get("suggested_analyses", [])
    schema        = module1_output.get("data_schema", {})

    suggestions_text = " ".join(str(s) for s in suggested).lower()

    # ── Priority 1: Explicit target keyword in column MEANING ──
    for col in df_columns:
        meaning = col_meanings.get(col, "").lower()
        if any(kw in meaning for kw in TARGET_MEANING_KEYWORDS):
            if not _is_non_target(col, col_meanings):
                return col, "meaning_keyword", 0.95

    # ── Priority 2: Explicit keyword in column NAME ──
    for col in df_columns:
        col_lower = col.lower().strip()
        for kw in TARGET_NAME_KEYWORDS:
            if re.search(rf'\b{re.escape(kw)}\b', col_lower):
                if not _is_non_target(col, col_meanings):
                    return col, "name_keyword", 0.85

    # ── Priority 3: Scan AI summary for prediction intent ──
    for col in df_columns:
        col_lower = col.lower()
        # Check if this column is mentioned near prediction language in summary
        if col_lower in ai_summary:
            context = _extract_context(ai_summary, col_lower, window=60)
            predict_words = ["predict", "forecast", "classify", "target", "outcome", "label"]
            if any(pw in context for pw in predict_words):
                if not _is_non_target(col, col_meanings):
                    return col, "ai_summary_scan", 0.75

    # ── Priority 4: Scan suggested analyses ──
    for col in df_columns:
        col_lower = col.lower()
        if col_lower in suggestions_text:
            # Check if it's used as the "thing being predicted"
            context = _extract_context(suggestions_text, col_lower, window=50)
            if any(pw in context for pw in ["by", "vs", "predict", "rate", "distribution"]):
                if not _is_non_target(col, col_meanings):
                    return col, "suggested_analyses", 0.65

    # ── Priority 5: Last column fallback ──
    # ML convention: last column is often the target
    # Filter out known non-targets
    candidates = [
        c for c in df_columns
        if not _is_non_target(c, col_meanings)
    ]
    if candidates:
        last = candidates[-1]
        return last, "last_column_fallback", 0.40

    # ── Absolute fallback ──
    return df_columns[-1], "absolute_fallback", 0.10


def get_feature_columns(
    df_columns: list,
    target_col: str,
    module1_output: dict
) -> Tuple[list, list]:
    """
    Split columns into features and columns to drop.

    Returns:
        (feature_columns, dropped_columns)
        feature_columns → columns to keep as model inputs
        dropped_columns → ID cols, all-text cols, etc.
    """
    col_meanings = module1_output.get("column_meanings", {})
    schema       = module1_output.get("data_schema", {})
    unknown_cols = schema.get("unknown", [])

    feature_cols = []
    dropped_cols = []

    for col in df_columns:
        if col == target_col:
            continue
        # Drop ID-like columns
        if _is_id_column(col, col_meanings):
            dropped_cols.append(col)
            continue
        # Drop unknown-type columns that are likely free text
        if col in unknown_cols:
            dropped_cols.append(col)
            continue
        feature_cols.append(col)

    return feature_cols, dropped_cols


def _is_non_target(col_name: str, col_meanings: dict) -> bool:
    """Returns True if this column is clearly NOT a target."""
    text = f"{col_name.lower()} {col_meanings.get(col_name, '').lower()}"
    return any(re.search(rf'\b{re.escape(kw)}\b', text) for kw in NON_TARGET_KEYWORDS)


def _is_id_column(col_name: str, col_meanings: dict) -> bool:
    id_keywords = ["id", "index", "uuid", "key", "identifier"]
    text = f"{col_name.lower()} {col_meanings.get(col_name, '').lower()}"
    return any(re.search(rf'\b{re.escape(kw)}\b', text) for kw in id_keywords)


def _extract_context(text: str, keyword: str, window: int = 60) -> str:
    """Extract text around a keyword for context scanning."""
    idx = text.find(keyword)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end   = min(len(text), idx + len(keyword) + window)
    return text[start:end]
