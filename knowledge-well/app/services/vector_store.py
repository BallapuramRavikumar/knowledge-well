
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import chromadb
from chromadb.config import Settings


os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY"] = "false"


class EmbeddingFunctionAdapter:
    def __init__(self, embedder):
        self.embedder = embedder
    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(input)

class VectorStore:
    def __init__(self, persist_path: str, collection_name: str, embedder) -> None:
        os.makedirs(persist_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_path, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=EmbeddingFunctionAdapter(embedder)
        )

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None):
        if ids is None:
            ids = [f"id-{i}" for i in range(len(texts))]
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        return self.collection.query(query_texts=[query_text], n_results=n_results)
