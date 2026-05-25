import pandas as pd


def detect_schema(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Analyzes the DataFrame to classify each column by its primary data type.
    
    The function classifies columns into four categories: numeric, datetime, categorical, and unknown.
    It attempts to parse object columns that resemble dates before falling back to categorical.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        
    Returns:
        dict[str, list[str]]: A dictionary mapping type labels ('numeric', 'categorical', 'datetime', 'unknown') to lists of column names.
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
    """
    Heuristic to determine if a pandas Series primarily contains datetime information.
    
    Args:
        series (pd.Series): The column data to analyze.
        
    Returns:
        bool: True if the column can be successfully parsed as datetime, False otherwise.
    """
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
    Heuristic to determine if a pandas Series is categorical based on cardinality.
    
    A column is considered categorical if it has low cardinality relative to the total number of rows.
    
    Args:
        series (pd.Series): The column data to analyze.
        
    Returns:
        bool: True if the column is likely categorical, False otherwise.
    """
    n_unique = series.nunique()
    n_total = len(series)
    return n_unique < 20 or (n_unique / n_total) < 0.1
