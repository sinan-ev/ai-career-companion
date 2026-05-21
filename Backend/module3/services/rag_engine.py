from ..services.context_builder import DataContext, get_context_chunks
from ..rag.embedding import Embedder
from ..rag.vector_store import VectorStore
from ..rag.retriever import Retriever, RetrievalResult

def build_rag(context: DataContext) -> tuple[VectorStore, Retriever]:
    """
    Initializes a localized RAG system populated with chunks from the dataset context.

    Args:
        context (DataContext): Structured dataset context data container.

    Returns:
        tuple[VectorStore, Retriever]: A tuple containing the created VectorStore and Retriever.
    """
    chunks = get_context_chunks(context)
    embedder = Embedder()
    store = VectorStore(embedder)
    store.add_texts(chunks)
    retriever = Retriever(store)
    return store, retriever

def retrieve_for_query(retriever: Retriever, query: str) -> str:
    """
    Runs similarity retrieval on the RAG system for a given query and returns raw context text.

    Args:
        retriever (Retriever): Active retriever instance.
        query (str): The search query.

    Returns:
        str: Concatenated text of matching document chunks.
    """
    res = retriever.retrieve(query)
    return res.context_text

def retrieve_for_plan(retriever: Retriever, plan: list[str]) -> RetrievalResult:
    """
    Runs similarity retrieval for each query in a plan, then combines unique matching chunks.

    Args:
        retriever (Retriever): Active retriever instance.
        plan (list[str]): List of query strings mapped from the analysis steps.

    Returns:
        RetrievalResult: Combined unique chunks and concatenated context text.
    """
    all_chunks = []
    for query in plan:
        res = retriever.retrieve(query)
        all_chunks.extend(res.chunks)
    all_chunks = list(set(all_chunks))
    return RetrievalResult(context_text="\n".join(all_chunks), chunks=all_chunks)
