import pandas as pd
from config import get_settings

settings = get_settings()


def maybe_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """
    If the dataset exceeds max_rows_before_sampling, return a
    stratified random sample. Otherwise return original df unchanged.

    Returns (df, was_sampled).
    """
    threshold = settings.max_rows_before_sampling
    sample_size = settings.sample_size

    if len(df) <= threshold:
        return df, False

    sampled = df.sample(
        n=min(sample_size, len(df)),
        random_state=42,
    ).reset_index(drop=True)

    return sampled, True