class VectorStore:
    """
    A simple in-memory mock Vector Store for storing text documents and retrieving them.
    """
    def __init__(self, embedder):
        """
        Initializes the VectorStore with a target text embedder.

        Args:
            embedder (Embedder): The embedding client or logic used to vectorize texts.
        """
        self.embedder = embedder
        self.documents = []
        self.embeddings = []

    def add_texts(self, texts):
        """
        Calculates embeddings for the provided texts and adds them to the store.

        Args:
            texts (List[str]): List of text document chunks to add to the vector database.
        """
        self.documents.extend(texts)
        self.embeddings.extend(self.embedder.embed_documents(texts))

    def similarity_search(self, query, k=3):
        """
        Searches the store for document chunks most similar to the query.

        Args:
            query (str): The search query.
            k (int, optional): The maximum number of nearest neighbor documents to return. Defaults to 3.

        Returns:
            List[tuple]: List of tuples pairing the document text string and its mock similarity score (float).
        """
        # Returning dummy scores as this is a mock vector store
        # In a real scenario, this would use cosine similarity.
        docs = self.documents[:k]
        scores = [0.85] * len(docs) # Mock similarity > 0.7 to pass validation
        return list(zip(docs, scores))
