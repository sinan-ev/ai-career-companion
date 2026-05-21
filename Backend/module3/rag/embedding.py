import numpy as np

class Embedder:
    """
    A utility class to generate mock vector embeddings for document texts and search queries.
    """

    def embed_documents(self, texts):
        """
        Generates vector embeddings for a list of document strings.

        Args:
            texts (List[str]): A list of text documents/chunks to embed.

        Returns:
            List[List[float]]: A list of 128-dimensional mock embedding vectors (random float values).
        """
        # Dummy implementation
        return [np.random.rand(128).tolist() for _ in texts]
    
    def embed_query(self, text):
        """
        Generates a vector embedding for a single text query string.

        Args:
            text (str): The query text to embed.

        Returns:
            List[float]: A single 128-dimensional mock embedding vector (random float values).
        """
        return np.random.rand(128).tolist()
