from dataclasses import dataclass
from typing import List

@dataclass
class RetrievalResult:
    context_text: str
    chunks: List[str]
    chunk_scores: List[tuple] = None

class Retriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, query: str) -> RetrievalResult:
        results = self.vector_store.similarity_search(query)
        chunks = [doc for doc, score in results]
        return RetrievalResult(
            context_text="\n".join(chunks), 
            chunks=chunks,
            chunk_scores=results
        )
