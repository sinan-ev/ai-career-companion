from pydantic import BaseModel
from typing import List, Dict, Any

class AnalyzeRequest(BaseModel):
    """
    Schema representing a request to analyze a dataset.

    Attributes:
        dataset_id (str): The unique identifier of the dataset to be analyzed.
        query (str): The specific question or analysis query to perform. Defaults to 'Give me a summary of this dataset'.
    """
    dataset_id: str
    query: str = "Give me a summary of this dataset"

class ChatRequest(BaseModel):
    """
    Schema representing a chat prompt or question against a dataset with history context.

    Attributes:
        dataset_id (str): The unique identifier of the dataset to query.
        query (str): The user's input message or question.
        history (List[Dict[str, str]]): List of previous chat messages in the conversation (role/content dicts). Defaults to an empty list.
    """
    dataset_id: str
    query: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    """
    Schema representing the system's chatbot response.

    Attributes:
        answer (str): The text response/answer produced by the chatbot.
        sources (List[str]): List of reference or background source documents/chunks used to build the answer.
    """
    answer: str
    sources: List[str]
