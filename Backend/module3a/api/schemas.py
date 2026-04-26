from pydantic import BaseModel
from typing import List, Dict, Any

class AnalyzeRequest(BaseModel):
    dataset_id: str
    query: str = "Give me a summary of this dataset"

class ChatRequest(BaseModel):
    dataset_id: str
    query: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
