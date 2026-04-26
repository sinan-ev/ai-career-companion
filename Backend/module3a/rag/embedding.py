import numpy as np

class Embedder:
    def embed_documents(self, texts):
        # Dummy implementation
        return [np.random.rand(128).tolist() for _ in texts]
    
    def embed_query(self, text):
        return np.random.rand(128).tolist()
