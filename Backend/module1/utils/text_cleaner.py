# utils/text_cleaner.py

import re


def clean_column_name(col: str) -> str:
    """
    Normalize a column name for keyword matching.
    e.g. 'PassengerId' → 'passengerid', 'fare_amount' → 'fare_amount'
    """
    col = col.lower().strip()
    col = re.sub(r"[^a-z0-9_]", "_", col)
    col = re.sub(r"_+", "_", col)
    return col


def extract_keywords(col: str) -> list[str]:
    """
    Split a column name into component keywords.
    e.g. 'hire_date' → ['hire', 'date']
         'CustomerID' → ['customer', 'id']
    """
    col = re.sub(r"([A-Z])", r"_\1", col).lower()
    parts = re.split(r"[^a-z0-9]", col)
    return [p for p in parts if len(p) > 1]