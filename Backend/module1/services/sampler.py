import pandas as pd
from module1.config import get_settings

settings = get_settings()


def maybe_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """
    Subsamples the dataset if it exceeds the configured maximum row threshold.
    
    This ensures that large datasets do not consume excessive memory or API tokens during profiling.
    
    Args:
        df (pd.DataFrame): The input pandas DataFrame.
        
    Returns:
        tuple[pd.DataFrame, bool]: A tuple containing the (potentially sampled) DataFrame and a boolean indicating whether sampling occurred.
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