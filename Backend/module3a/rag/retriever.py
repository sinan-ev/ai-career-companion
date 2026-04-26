from dataclasses import dataclass
from typing import List

@dataclass
class RetrievalResult:
    context_text: str
    chunks: List[str]

class Retriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, query: str) -> RetrievalResult:
        chunks = self.vector_store.similarity_search(query)
        return RetrievalResult(context_text="\n".join(chunks), chunks=chunks)
