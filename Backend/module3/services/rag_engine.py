from ..services.context_builder import DataContext, get_context_chunks
from ..rag.embedding import Embedder
from ..rag.vector_store import VectorStore
from ..rag.retriever import Retriever, RetrievalResult

def build_rag(context: DataContext) -> tuple[VectorStore, Retriever]:
    chunks = get_context_chunks(context)
    embedder = Embedder()
    store = VectorStore(embedder)
    store.add_texts(chunks)
    retriever = Retriever(store)
    return store, retriever

def retrieve_for_query(retriever: Retriever, query: str) -> str:
    res = retriever.retrieve(query)
    return res.context_text

def retrieve_for_plan(retriever: Retriever, plan: list[str]) -> RetrievalResult:
    all_chunks = []
    for query in plan:
        res = retriever.retrieve(query)
        all_chunks.extend(res.chunks)
    all_chunks = list(set(all_chunks))
    return RetrievalResult(context_text="\n".join(all_chunks), chunks=all_chunks)
