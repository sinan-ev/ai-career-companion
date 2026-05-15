from pydantic import BaseModel
from typing import List, Dict, Any

class ChartData(BaseModel):
    type: str
    title: str
    analysis_type: str
    figure: Dict[str, Any]

class DatasetSummary(BaseModel):
    row_count: int
    column_count: int
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]

class Module3Result(BaseModel):
    charts: List[ChartData]
    insights: List[str]
    explanations: str
    analysis_plan: List[str]
    stats: Dict[str, Any]
    chat_response: str
    confidence_score: float
    rag_context: str
    dataset_summary: DatasetSummary
