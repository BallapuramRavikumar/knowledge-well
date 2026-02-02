from __future__ import annotations
from typing import List
from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu", batch_size: int = 32):
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], batch_size=1, normalize_embeddings=True)[0].tolist()
