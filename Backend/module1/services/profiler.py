import pandas as pd
import numpy as np
from module1.models.response_model import DataQuality

# All the disguised null values seen in real datasets
EXTENDED_NULL_VALUES = {
    # String nulls
    "", " ", "  ",
    "nan", "NaN", "NAN",
    "null", "NULL", "Null",
    "none", "None", "NONE",
    "na", "NA", "N/A", "n/a", "N/a",
    "nil", "NIL", "Nil",
    # Common placeholders
    "-", "--", "---",
    "?", "??",
    "missing", "Missing", "MISSING",
    "unknown", "Unknown", "UNKNOWN",
    "undefined", "Undefined",
    "not available", "Not Available",
    "not applicable", "Not Applicable",
    # Numeric sentinels
    "999", "9999", "-999", "-9999",
    "99", "-1", "0",
}

NUMERIC_SENTINEL_VALUES = {999, 9999, -999, -9999, -1}


def normalize_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces disguised null values (e.g., 'NA', '?', '-999') with real NaNs.
    
    This helps pandas correctly identify and compute missing value metrics.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        
    Returns:
        pd.DataFrame: A new DataFrame with normalized null values.
    """
    # Step 1 — replace known string nulls in object columns
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        # strip whitespace first, then check against null set
        df[col] = df[col].apply(
            lambda x: np.nan
            if isinstance(x, str) and x.strip().lower() in {
                v.lower() for v in EXTENDED_NULL_VALUES
            }
            else x
        )

    # Step 2 — replace numeric sentinel values in numeric columns
    for col in df.select_dtypes(include="number").columns:
        sentinel_count = df[col].isin(NUMERIC_SENTINEL_VALUES).sum()
        # Only replace if sentinels make up less than 50% of values
        # (avoids replacing a column where -1 is a real value)
        if 0 < sentinel_count < len(df[col]) * 0.5:
            df[col] = df[col].replace(
                list(NUMERIC_SENTINEL_VALUES), np.nan
            )

    return df


def profile_dataset(df: pd.DataFrame) -> DataQuality:
    """
    Profiles data quality by computing missing values and duplicates.
    
    Args:
        df (pd.DataFrame): The input DataFrame to be profiled.
        
    Returns:
        DataQuality: A pydantic model containing missing value counts, percentages, duplicate rows, and total row count.
    """
    # Normalize first — catch all types of null
    df_clean = normalize_nulls(df)

    total_rows = len(df_clean)
    missing_values: dict[str, int] = {}
    missing_percent: dict[str, float] = {}

    for col in df_clean.columns:
        n_missing = int(df_clean[col].isna().sum())
        if n_missing > 0:
            missing_values[col] = n_missing
            missing_percent[col] = round(
                (n_missing / total_rows) * 100, 2
            )

    duplicate_rows = int(df_clean.duplicated().sum())

    return DataQuality(
        missing_values=missing_values,
        missing_percent=missing_percent,
        duplicate_rows=duplicate_rows,
        total_rows=total_rows,
    )


def get_basic_stats(df: pd.DataFrame) -> dict:
    """
    Computes summary statistics for numeric columns in the dataset.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        
    Returns:
        dict: A dictionary of summary statistics, suitable for JSON serialization.
    """
    from fastapi.encoders import jsonable_encoder
    df_clean = normalize_nulls(df)
    numeric_cols = df_clean.select_dtypes(include="number")
    if numeric_cols.empty:
        return {}
    
    # describe().to_dict() contains numpy types; jsonable_encoder fixes them
    stats = numeric_cols.describe().round(2).to_dict()
    return jsonable_encoder(stats)











def generate_cleaning_suggestions(
    df: pd.DataFrame,
    schema: dict[str, list[str]],
    column_meanings: dict[str, str],
) -> list[str]:
    """
    Suggests column name and data type fixes to the user based on heuristics.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        schema (dict[str, list[str]]): The identified dataset schema.
        column_meanings (dict[str, str]): The inferred meanings of the columns.
        
    Returns:
        list[str]: A list of actionable cleaning suggestions.
    """
    suggestions = []

    for col in df.columns:

        # 1. Unreadable column names
        if _is_unreadable_name(col):
            clean = col.replace("_", " ").replace("-", " ").title()
            suggestions.append(
                f"Column '{col}' has an unreadable name — consider renaming to '{clean}'"
            )

        # 2. Columns in 'unknown' type
        if col in schema.get("unknown", []):
            suggestions.append(
                f"Column '{col}' has an unknown type — check if it should be numeric or categorical"
            )

        # 3. Numeric columns stored as text
        if col in schema.get("categorical", []):
            sample = df[col].dropna().head(20)
            numeric_count = sum(
                1 for v in sample
                if str(v).replace(".", "").replace("-", "").isdigit()
            )
            if numeric_count > 15:  # 75%+ look like numbers
                suggestions.append(
                    f"Column '{col}' looks numeric but is stored as text — "
                    f"consider converting with pd.to_numeric(df['{col}'])"
                )

        # 4. ID columns that shouldn't be analyzed
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["id", "uuid", "index", "key"]):
            if col in schema.get("numeric", []):
                suggestions.append(
                    f"Column '{col}' looks like an ID — consider dropping it before modeling"
                )

        # 5. Columns with meaning 'Unknown'
        meaning = column_meanings.get(col, "")
        if "unknown" in meaning.lower():
            suggestions.append(
                f"Column '{col}' meaning could not be determined — "
                f"consider renaming it to something descriptive"
            )

    return suggestions


def _is_unreadable_name(col: str) -> bool:
    """
    Determines if a column name looks machine-generated or unreadable.
    
    Args:
        col (str): The column name to check.
        
    Returns:
        bool: True if the name appears unreadable (e.g., 'var_001'), False otherwise.
    """
    import re
    # All lowercase single letter + number like x1, v2
    if re.match(r'^[a-zA-Z]{1,3}\d+$', col):
        return True
    # Contains no vowels (likely abbreviation like 'psgr_cnt')
    letters = [c for c in col.lower() if c.isalpha()]
    if len(letters) > 3 and not any(v in letters for v in 'aeiou'):
        return True
    return False
