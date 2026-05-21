from dataclasses import dataclass
from typing import List

@dataclass
class RetrievalResult:
    """
    Data container representing the output of a similarity retrieval operation.

    Attributes:
        context_text (str): Concatenated text of all retrieved document chunks.
        chunks (List[str]): List of individual retrieved text chunks.
        chunk_scores (List[tuple]): List of tuples containing chunk text and their corresponding similarity score. Defaults to None.
    """
    context_text: str
    chunks: List[str]
    chunk_scores: List[tuple] = None

class Retriever:
    """
    A search class wrapper that executes queries against a VectorStore and compiles results.
    """
    def __init__(self, vector_store):
        """
        Initializes the Retriever with a target vector store.

        Args:
            vector_store (VectorStore): The underlying vector store object to run queries against.
        """
        self.vector_store = vector_store

    def retrieve(self, query: str) -> RetrievalResult:
        """
        Queries the vector store for semantic matches and aggregates the results.

        Args:
            query (str): The text query or question.

        Returns:
            RetrievalResult: Compiled context text and list of chunks with similarity scores.
        """
        results = self.vector_store.similarity_search(query)
        chunks = [doc for doc, score in results]
        return RetrievalResult(
            context_text="\n".join(chunks), 
            chunks=chunks,
            chunk_scores=results
        )
