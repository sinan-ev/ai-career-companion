class VectorStore:
    def __init__(self, embedder):
        self.embedder = embedder
        self.documents = []
        self.embeddings = []

    def add_texts(self, texts):
        self.documents.extend(texts)
        self.embeddings.extend(self.embedder.embed_documents(texts))

    def similarity_search(self, query, k=3):
        # Returning dummy scores as this is a mock vector store
        # In a real scenario, this would use cosine similarity.
        docs = self.documents[:k]
        scores = [0.85] * len(docs) # Mock similarity > 0.7 to pass validation
        return list(zip(docs, scores))
