class VectorStore:
    def __init__(self, embedder):
        self.embedder = embedder
        self.documents = []
        self.embeddings = []

    def add_texts(self, texts):
        self.documents.extend(texts)
        self.embeddings.extend(self.embedder.embed_documents(texts))

    def similarity_search(self, query, k=3):
        return self.documents[:k]
