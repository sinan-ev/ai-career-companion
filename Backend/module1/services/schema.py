import pandas as pd


def detect_schema(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Classify every column into: numeric, categorical, datetime, unknown.
    Also attempts to parse object columns that look like dates.
    """
    schema = {
        "numeric": [],
        "categorical": [],
        "datetime": [],
        "unknown": [],
    }

    for col in df.columns:
        dtype = df[col].dtype

        if pd.api.types.is_numeric_dtype(dtype):
            schema["numeric"].append(col)

        elif pd.api.types.is_datetime64_any_dtype(dtype):
            schema["datetime"].append(col)

        elif dtype == object:
            # Try parsing as datetime before calling it categorical
            if _looks_like_datetime(df[col]):
                schema["datetime"].append(col)

            elif _looks_like_categorical(df[col]):
                schema["categorical"].append(col)

            else:
                schema["unknown"].append(col)

        else:
            schema["unknown"].append(col)

    return schema



def _looks_like_datetime(series: pd.Series) -> bool:
    
    sample = series.dropna().head(50)
    if len(sample) == 0:
        return False
    try:
        # pd.to_datetime(sample)
        pd.to_datetime(sample, format="mixed", dayfirst=False)
        return True
    
    except Exception:
        return False


def _looks_like_categorical(series: pd.Series) -> bool:
    """
    A column is categorical if it has low cardinality
    relative to total rows (< 10% unique or < 20 unique values).
    """
    n_unique = series.nunique()
    n_total = len(series)
    return n_unique < 20 or (n_unique / n_total) < 0.1