

import pandas as pd
from typing import List, Tuple


# ─────────────────────────────────────────────
#  CUSTOM EXCEPTION
# ─────────────────────────────────────────────

class ValidationError(Exception):
    """
    Raised when Module 2 inputs fail a fatal check.
    Pipeline stops immediately when this is raised.
    """
    pass


# ─────────────────────────────────────────────
#  REQUIRED MODULE 1 FIELDS
# ─────────────────────────────────────────────

# These are the exact fields Module 1's AnalysisResponse always returns.
# If any are missing, we cannot safely run the pipeline.
REQUIRED_MODULE1_FIELDS = [
    "dataset_info",
    "data_schema",
    "column_meanings",
    "data_quality",
    "ai_summary",
    "suggested_analyses",
    "warnings",
]

# These sub-keys must exist inside module1_output["data_schema"]
REQUIRED_SCHEMA_KEYS = ["numeric", "categorical", "datetime", "unknown"]

# These sub-keys must exist inside module1_output["data_quality"]
REQUIRED_QUALITY_KEYS = ["missing_values", "missing_percent", "duplicate_rows", "total_rows"]


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def validate_inputs(
    df: pd.DataFrame,
    module1_output: dict
) -> Tuple[List[str], List[str]]:
    """
    Validate both inputs before the pipeline starts.

    Args:
        df             : DataFrame loaded from the user's file
        module1_output : Complete output dict from Module 1

    Returns:
        (errors, warnings)
        errors   → fatal issues — pipeline must stop
        warnings → non-fatal issues — pipeline continues, user is informed

    Usage:
        errors, warnings = validate_inputs(df, module1_output)
        if errors:
            raise ValidationError(errors[0])
    """
    errors = []
    warnings = []

    # ── 1. Validate the DataFrame ──
    df_errors, df_warnings = _validate_dataframe(df)
    errors.extend(df_errors)
    warnings.extend(df_warnings)

    # ── 2. Validate Module 1 output structure ──
    m1_errors, m1_warnings = _validate_module1_output(module1_output)
    errors.extend(m1_errors)
    warnings.extend(m1_warnings)

    # ── 3. Cross-validate: schema columns vs DataFrame columns ──
    # Only run if both are valid so far
    if not errors:
        cross_errors, cross_warnings = _cross_validate(df, module1_output)
        errors.extend(cross_errors)
        warnings.extend(cross_warnings)

    return errors, warnings


# ─────────────────────────────────────────────
#  DATAFRAME VALIDATION
# ─────────────────────────────────────────────

def _validate_dataframe(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    errors = []
    warnings = []

    # Fatal: not even a DataFrame
    if not isinstance(df, pd.DataFrame):
        errors.append(
            f"Expected a Pandas DataFrame but received {type(df).__name__}."
        )
        return errors, warnings

    # Fatal: completely empty
    if df.shape[0] == 0:
        errors.append(
            "DataFrame has 0 rows. Cannot run preprocessing on empty data."
        )

    # Fatal: no columns at all
    if df.shape[1] == 0:
        errors.append(
            "DataFrame has 0 columns. Nothing to process."
        )

    # Fatal: duplicate column names (breaks encoding, scaling, everything)
    duplicate_cols = df.columns[df.columns.duplicated()].tolist()
    if duplicate_cols:
        errors.append(
            f"DataFrame has duplicate column names: {duplicate_cols}. "
            f"Rename them before running Module 2."
        )

    # Warning: very few rows
    if df.shape[0] < 10 and df.shape[0] > 0:
        warnings.append(
            f"DataFrame has only {df.shape[0]} rows. "
            f"Results may be unreliable with such small data."
        )

    # Warning: very many columns
    if df.shape[1] > 100:
        warnings.append(
            f"DataFrame has {df.shape[1]} columns. "
            f"Feature selection is strongly recommended."
        )

    # Warning: entirely null columns
    all_null_cols = [c for c in df.columns if df[c].isnull().all()]
    if all_null_cols:
        warnings.append(
            f"These columns are 100% null and will be dropped: {all_null_cols}"
        )

    return errors, warnings


# ─────────────────────────────────────────────
#  MODULE 1 OUTPUT VALIDATION
# ─────────────────────────────────────────────

def _validate_module1_output(module1_output: dict) -> Tuple[List[str], List[str]]:
    errors = []
    warnings = []

    # Fatal: not a dict at all
    if not isinstance(module1_output, dict):
        errors.append(
            f"module1_output must be a dict but received {type(module1_output).__name__}. "
            f"Pass the full output from Module 1's run_pipeline()."
        )
        return errors, warnings

    # Fatal: missing required top-level fields
    missing_fields = [f for f in REQUIRED_MODULE1_FIELDS if f not in module1_output]
    if missing_fields:
        errors.append(
            f"module1_output is missing required fields: {missing_fields}. "
            f"Make sure you pass the complete Module 1 output."
        )
        return errors, warnings

    # ── Validate schema ──
    schema = module1_output.get("data_schema", {})
    if not isinstance(schema, dict):
        errors.append(
            f"module1_output['schema'] must be a dict but got {type(schema).__name__}."
        )
    else:
        missing_schema_keys = [k for k in REQUIRED_SCHEMA_KEYS if k not in schema]
        if missing_schema_keys:
            errors.append(
                f"module1_output['schema'] is missing keys: {missing_schema_keys}. "
                f"Expected keys: {REQUIRED_SCHEMA_KEYS}."
            )
        # Warning: all schema lists are empty (no columns classified)
        all_cols = (
            schema.get("numeric", []) +
            schema.get("categorical", []) +
            schema.get("datetime", []) +
            schema.get("unknown", [])
        )
        if len(all_cols) == 0:
            warnings.append(
                "module1_output['schema'] has no columns classified. "
                "Schema detection in Module 1 may have failed."
            )

    # ── Validate data_quality ──
    quality = module1_output.get("data_quality", {})
    if not isinstance(quality, dict):
        errors.append(
            f"module1_output['data_quality'] must be a dict but got {type(quality).__name__}."
        )
    else:
        missing_quality_keys = [k for k in REQUIRED_QUALITY_KEYS if k not in quality]
        if missing_quality_keys:
            warnings.append(
                f"module1_output['data_quality'] is missing keys: {missing_quality_keys}. "
                f"Some EDA enrichment will be skipped."
            )

    # ── Validate column_meanings ──
    meanings = module1_output.get("column_meanings", {})
    if not isinstance(meanings, dict):
        errors.append(
            f"module1_output['column_meanings'] must be a dict "
            f"but got {type(meanings).__name__}."
        )
    elif len(meanings) == 0:
        warnings.append(
            "module1_output['column_meanings'] is empty. "
            "Target detection and smart imputation will fall back to heuristics."
        )

    # ── Validate ai_summary ──
    summary = module1_output.get("ai_summary", "")
    if not isinstance(summary, str) or len(summary.strip()) == 0:
        warnings.append(
            "module1_output['ai_summary'] is empty. "
            "Agent planner will work without domain context."
        )

    return errors, warnings


# ─────────────────────────────────────────────
#  CROSS VALIDATION
# ─────────────────────────────────────────────

def _cross_validate(
    df: pd.DataFrame,
    module1_output: dict
) -> Tuple[List[str], List[str]]:
    """
    Cross-check that the schema columns actually exist in the DataFrame.

    Module 1 detects schema on the original file.
    Module 2 receives the same file loaded as a DataFrame.
    They should match — but if there was any preprocessing between
    modules, column names might differ.
    """
    errors = []
    warnings = []

    schema = module1_output.get("data_schema", {})
    df_columns = set(df.columns.tolist())

    # All columns mentioned in any schema list
    schema_cols = set(
        schema.get("numeric", []) +
        schema.get("categorical", []) +
        schema.get("datetime", []) +
        schema.get("unknown", [])
    )

    # Columns in schema but missing from DataFrame
    missing_from_df = schema_cols - df_columns
    if missing_from_df:
        warnings.append(
            f"These columns are in Module 1's schema but not in the DataFrame: "
            f"{sorted(missing_from_df)}. They will be ignored during processing."
        )

    # Columns in DataFrame but not in any schema list
    missing_from_schema = df_columns - schema_cols
    if missing_from_schema:
        warnings.append(
            f"These columns are in the DataFrame but not in Module 1's schema: "
            f"{sorted(missing_from_schema)}. They will be treated as 'unknown' type."
        )

    # Fatal: no overlap at all between schema and DataFrame
    overlap = schema_cols & df_columns
    if len(schema_cols) > 0 and len(overlap) == 0:
        errors.append(
            "No columns from Module 1's schema match the DataFrame columns. "
            "Make sure the same file is passed to both modules."
        )

    # Check dataset_info row count vs actual DataFrame rows
    dataset_info = module1_output.get("dataset_info", {})
    m1_rows = dataset_info.get("rows", 0)
    df_rows = len(df)

    # Allow for sampling: Module 1 might have sampled to 5000 rows
    # so df might be smaller. Only warn if df is LARGER (shouldn't happen).
    if m1_rows > 0 and df_rows > m1_rows * 1.1:
        warnings.append(
            f"DataFrame has {df_rows} rows but Module 1 reported {m1_rows} rows. "
            f"Make sure you're passing the same dataset."
        )

    return errors, warnings


# ─────────────────────────────────────────────
#  CONVENIENCE FUNCTION
# ─────────────────────────────────────────────

def validate_or_raise(df: pd.DataFrame, module1_output: dict) -> List[str]:
    """
    Convenience wrapper — raises ValidationError on any fatal error.
    Returns warnings list so the pipeline can pass them to Module2Response.

    Usage (simplest form in pipeline_module2.py):
        warnings = validate_or_raise(df, module1_output)
        # if we reach here, inputs are safe to process
    """
    errors, warnings = validate_inputs(df, module1_output)
    if errors:
        raise ValidationError(
            f"Module 2 validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    return warnings
