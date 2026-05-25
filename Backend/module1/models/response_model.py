from pydantic import BaseModel
from typing import Optional


class DatasetInfo(BaseModel):
    """
    Basic information about the processed dataset.
    
    Attributes:
        rows (int): Total number of rows in the dataset.
        columns (int): Total number of columns in the dataset.
        domain (str): Detected domain or industry of the dataset.
        dataset_type (str): Type of the dataset (e.g., Tabular, Time Series).
        file_name (str): The name of the processed file.
        was_sampled (bool): Indicates if the dataset was sampled down for processing.
    """
    rows: int
    columns: int
    domain: str
    dataset_type: str
    file_name: str
    was_sampled: bool


class SchemaInfo(BaseModel):
    """
    Schema information detailing the data types of columns.
    
    Attributes:
        numeric (list[str]): List of column names that contain numeric data.
        categorical (list[str]): List of column names that contain categorical data.
        datetime (list[str]): List of column names that contain datetime data.
        unknown (list[str]): List of column names with undetermined data types.
    """
    numeric: list[str]
    categorical: list[str]
    datetime: list[str]
    unknown: list[str]


class DataQuality(BaseModel):
    """
    Quality metrics for the dataset.
    
    Attributes:
        missing_values (dict[str, int]): Mapping of column names to the count of missing values.
        missing_percent (dict[str, float]): Mapping of column names to the percentage of missing values.
        duplicate_rows (int): Number of duplicate rows detected in the dataset.
        total_rows (int): Total number of rows evaluated.
    """
    missing_values: dict[str, int]       # col → count
    missing_percent: dict[str, float]    # col → percent
    duplicate_rows: int
    total_rows: int


class AnalysisResponse(BaseModel):
    """
    The main response model encapsulating the full analysis of the dataset.
    
    Attributes:
        dataset_info (DatasetInfo): Summary information about the dataset.
        data_schema (SchemaInfo): Discovered schema and data types.
        column_meanings (dict[str, str]): Mapping of column names to their inferred meanings.
        data_quality (DataQuality): Metrics outlining the quality of the data.
        ai_summary (str): AI-generated summary of the dataset.
        suggested_analyses (list[str]): List of AI-suggested analytical steps or models.
        warnings (list[str]): Any warnings or cleaning suggestions generated during processing.
    """
    dataset_info: DatasetInfo
    data_schema: SchemaInfo
    column_meanings: dict[str, str]      # col → plain English meaning
    data_quality: DataQuality
    # type_suggestions: dict[str, str]     # col → suggestion
    ai_summary: str
    suggested_analyses: list[str]
    warnings: list[str]
