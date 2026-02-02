
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..core.config import settings
from ..services.embedder import Embedder
from ..services.vector_store import VectorStore

router = APIRouter()

_embedder = None
_vs = None

def get_vs():
    global _embedder, _vs
    if _embedder is None:
        _embedder = Embedder(settings.EMBEDDING_MODEL, settings.DEVICE, settings.EMBED_BATCH)
    if _vs is None:
        _vs = VectorStore(settings.VECTORSTORE_PATH, settings.VECTOR_COLLECTION, _embedder)
    return _vs

class QueryRequest(BaseModel):
    query: str
    k: Optional[int] = 5

@router.post("/query")
def query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    vs = get_vs()
    hits = vs.query(req.query, n_results=req.k or 5)
    return {"results": hits}
#   Inti  py Return { "results : hits"
