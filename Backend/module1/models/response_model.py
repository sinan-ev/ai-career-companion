from pydantic import BaseModel
from typing import Optional


class DatasetInfo(BaseModel):
    rows: int
    columns: int
    domain: str
    dataset_type: str
    file_name: str
    was_sampled: bool


class SchemaInfo(BaseModel):
    numeric: list[str]
    categorical: list[str]
    datetime: list[str]
    unknown: list[str]


class DataQuality(BaseModel):
    missing_values: dict[str, int]       # col → count
    missing_percent: dict[str, float]    # col → percent
    duplicate_rows: int
    total_rows: int


class AnalysisResponse(BaseModel):
    dataset_info: DatasetInfo
    data_schema: SchemaInfo
    column_meanings: dict[str, str]      # col → plain English meaning
    data_quality: DataQuality
    # type_suggestions: dict[str, str]     # col → suggestion
    ai_summary: str
    suggested_analyses: list[str]
    warnings: list[str]