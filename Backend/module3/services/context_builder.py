# Converts raw dataset → structured knowledge

from typing import Any, Dict, List
import pandas as pd
from dataclasses import dataclass

@dataclass
class DataContext:
    """
    Data container representing the structured knowledge context of a dataset.

    Attributes:
        dataset_name (str): The logical name of the dataset.
        dataset_description (str): A business explanation of the dataset's purpose.
        numeric_columns (List[str]): List of column names that contain numeric data.
        categorical_columns (List[str]): List of column names containing categorical/string values.
        datetime_columns (List[str]): List of column names containing datetime values.
        column_meanings (Dict[str, str]): A map of column names to their semantic description/meaning.
    """
    dataset_name: str
    dataset_description: str
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    column_meanings: Dict[str, str]

def build_context(module1_output: Dict[str, Any], module2_output: Dict[str, Any]) -> DataContext:
    """
    Constructs a DataContext object by merging outputs from Module 1 and Module 2.

    Args:
        module1_output (Dict[str, Any]): Metadata output dictionary from Module 1.
        module2_output (Dict[str, Any]): Context dictionary from Module 2.

    Returns:
        DataContext: The structured semantic dataset representation.
    """
    summary = module1_output.get("dataset_summary", {})
    return DataContext(
        dataset_name=module1_output.get("dataset_name", "Dataset"),
        dataset_description=summary.get("description", "A dataset"),
        numeric_columns=summary.get("numeric_columns", []),
        categorical_columns=summary.get("categorical_columns", []),
        datetime_columns=summary.get("datetime_columns", []),
        column_meanings=summary.get("column_meanings", {})
    )

def get_context_chunks(context: DataContext) -> List[str]: #These chunks go into:RAG(vector database) ,DataContext → RAG → LLM
    """
    Splits the structured dataset context into distinct text chunks suitable for embedding indexing.

    Args:
        context (DataContext): Structured dataset context data container.

    Returns:
        List[str]: A list of text chunk strings representing dataset facts.
    """
    chunks = [f"Dataset Name: {context.dataset_name}"]
    chunks.append(f"Description: {context.dataset_description}")
    for col, meaning in context.column_meanings.items():
        chunks.append(f"Column '{col}': {meaning}")
    return chunks
