import pandas as pd
from pathlib import Path
from utils.constants import ALLOWED_EXTENSIONS


class ValidationError(Exception):
    pass


def validate_dataset(df: pd.DataFrame, filename: str) -> list[str]:
    """
    Run all validation checks. Returns a list of warnings (non-fatal).
    Raises ValidationError on fatal problems.
    """

    warnings = []

    # 1. File extension
    suffix = Path(filename).suffix.lower()
    
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{suffix}' not supported. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Empty dataset
    if df.empty:
        raise ValidationError("Dataset is empty — no rows found.")

    # 3. No columns
    if len(df.columns) == 0:
        raise ValidationError("Dataset has no columns.")

    # 4. Duplicate column names
    dupes = df.columns[df.columns.duplicated()].tolist()
    if dupes:
        raise ValidationError(f"Duplicate column names found: {dupes}")

    # 5. Soft warnings (non-fatal)
    if len(df) < 10:
        warnings.append("Dataset has fewer than 10 rows — results may be unreliable.")

    if len(df.columns) > 100:
        warnings.append("Dataset has more than 100 columns — analysis may be slow.")

    high_missing = [
        col for col in df.columns
        if df[col].isna().mean() > 0.5
    ]
    if high_missing:
        warnings.append(
            f"These columns have >50% missing values: {high_missing}"
        )

    return warnings