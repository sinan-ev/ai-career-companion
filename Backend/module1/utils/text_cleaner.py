# utils/text_cleaner.py

import re


def clean_column_name(col: str) -> str:
    """
    Normalizes a column name to facilitate keyword matching.
    
    Converts the name to lowercase, replaces non-alphanumeric characters with underscores, 
    and removes redundant underscores.
    
    Args:
        col (str): The raw column name.
        
    Returns:
        str: The cleaned and normalized column name.
    """
    col = col.lower().strip()
    col = re.sub(r"[^a-z0-9_]", "_", col)
    col = re.sub(r"_+", "_", col)
    return col


def extract_keywords(col: str) -> list[str]:
    """
    Splits a complex column name into component keywords.
    
    Handles CamelCase and snake_case formats.
    
    Args:
        col (str): The raw column name.
        
    Returns:
        list[str]: A list of lowercase keywords extracted from the column name.
    """
    col = re.sub(r"([A-Z])", r"_\1", col).lower()
    parts = re.split(r"[^a-z0-9]", col)
    return [p for p in parts if len(p) > 1]
