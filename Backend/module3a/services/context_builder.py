from typing import Any, Dict, List
import pandas as pd
from dataclasses import dataclass

@dataclass
class DataContext:
    dataset_name: str
    dataset_description: str
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    column_meanings: Dict[str, str]

def build_context(module1_output: Dict[str, Any], module2_output: Dict[str, Any]) -> DataContext:
    summary = module1_output.get("dataset_summary", {})
    return DataContext(
        dataset_name=module1_output.get("dataset_name", "Dataset"),
        dataset_description=summary.get("description", "A dataset"),
        numeric_columns=summary.get("numeric_columns", []),
        categorical_columns=summary.get("categorical_columns", []),
        datetime_columns=summary.get("datetime_columns", []),
        column_meanings=summary.get("column_meanings", {})
    )

def get_context_chunks(context: DataContext) -> List[str]:
    chunks = [f"Dataset Name: {context.dataset_name}"]
    chunks.append(f"Description: {context.dataset_description}")
    for col, meaning in context.column_meanings.items():
        chunks.append(f"Column '{col}': {meaning}")
    return chunks
