from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.exceptions import ToolError

# --- All imports from your `app` directory ---
from app.core.config import settings
from app.services.embedder import Embedder
from app.services.vector_store import VectorStore
from app.services.graphdb import GraphDBClient
from app.services.query_rewriter import QueryRewriter
from app.services.ollama_client import OllamaClient
from app.services.openai_client import OpenAIClient
from app.services.gemini_client import GeminiClient
from app.services.rag import (
    build_prompt,
    build_graph_problem_context,
    extract_keywords,
)

_embedder: Optional[Embedder] = None
_vs: Optional[VectorStore] = None
_graph: Optional[GraphDBClient] = None
_llm: Optional[OllamaClient | OpenAIClient | GeminiClient] = None
_rewriter: Optional[QueryRewriter] = None


def get_components():
    """Initializes all RAG components in a thread-safe way."""
    global _embedder, _vs, _graph, _llm, _rewriter

    # Use a lock to ensure only one thread initializes components at a time
    _lock: asyncio.Lock = asyncio.Lock()

    async def init_async():
        async with _lock:
            nonlocal _embedder, _vs, _graph, _llm, _rewriter
            if _embedder is None:
                _embedder = Embedder(settings.EMBEDDING_MODEL, settings.DEVICE, settings.EMBED_BATCH)
            if _vs is None:
                _vs = VectorStore(settings.VECTORSTORE_PATH, settings.VECTOR_COLLECTION, _embedder)
            if _graph is None:
                _graph = GraphDBClient(
                    base_url=settings.GRAPHDB_BASE_URL,
                    repository=settings.GRAPHDB_REPOSITORY,
                    auth_mode=settings.GRAPHDB_AUTH,
                    username=settings.GRAPHDB_USERNAME,
                    password=settings.GRAPHDB_PASSWORD,
                    verify_tls=settings.GRAPHDB_VERIFY_TLS,
                    timeout=settings.GRAPHDB_TIMEOUT,
                    token_ttl_seconds=settings.GRAPHDB_TOKEN_TTL_SECONDS,
                )
            if _llm is None:
                prov = settings.LLM_PROVIDER.upper()
                if prov == "OPENAI":
                    _llm = OpenAIClient(
                        api_key=settings.OPENAI_API_KEY,
                        model=settings.OPENAI_MODEL,
                        base_url=settings.OPENAI_BASE_URL,
                        timeout_seconds=settings.OPENAI_TIMEOUT_SECONDS,
                        use_responses_api=settings.OPENAI_USE_RESPONSES,
                    )
                elif prov == "GEMINI":
                    _llm = GeminiClient(
                        api_key=settings.GEMINI_API_KEY,
                        model=settings.GEMINI_MODEL,
                        timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
                    )
                else:
                    _llm = OllamaClient(
                        base_url=settings.OLLAMA_BASE_URL,
                        model=settings.OLLAMA_MODEL
                    )

            if _rewriter is None and settings.USE_LLM_REWRITER and settings.REWRITER_PROVIDER.upper() == "OPENAI":
                _rewriter = QueryRewriter(model=settings.REWRITER_MODEL,
                                          timeout_seconds=settings.REWRITER_TIMEOUT_SECONDS)

    asyncio.run(init_async())
    return _vs, _graph, _llm, _rewriter


# Initialize the MCP Server
mcp = FastMCP("KnowledgeWellRAG")


@mcp.tool()
def chat_rag(question: str, k: int = 5, temperature: float = 0.2) -> str:
    """
    Answers questions by retrieving information from a GraphDB knowledge graph and a vector store.

    Args:
        question: The user's question to be answered.
        k: The number of documents to retrieve from the vector store.
        temperature: The temperature for the language model.
    """
    if not question.strip():
        raise ToolError("Question cannot be empty.")

    vs, graph, llm, rewriter = get_components()

    # Vector hits
    try:
        hits = vs.query(question, n_results=k)
    except Exception as e:
        hits = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}

    # Heuristic + optional rewriter
    terms = extract_keywords(question)
    if settings.USE_LLM_REWRITER and rewriter is not None:
        try:
            rw_out = rewriter.rewrite(question)
            llm_terms = (rw_out.get("domain_phrases", []) or []) + (rw_out.get("keywords", []) or [])
            seen = set(t.lower() for t in terms)
            for t in llm_terms:
                if t.lower() not in seen:
                    terms.append(t)
                    seen.add(t.lower())
        except Exception:
            pass  # Fail open

    if not terms:
        return "I couldn’t extract domain terms from your question. Please include key phrases (e.g., “hybrid bonding”, “advanced packaging”)."

    # Graph context
    gctx, _ = build_graph_problem_context(
        graph, question,
        probe=True,
        include_summaries=True,
        include_content_parts=True,
        include_goal_achieved=True
    )

    # LLM answer
    prompt = build_prompt(question, hits, gctx)

    try:
        answer, _ = llm.generate(
            prompt,
            system="You are a precise RAG assistant; cite sources.",
            temperature=temperature,
            return_meta=True,
        )
        return answer
    except TypeError:
        # Some clients may not support return_meta
        answer = llm.generate(
            prompt,
            system="You are a precise RAG assistant; cite sources.",
            temperature=temperature,
        )
        return answer


if __name__ == "__main__":
    mcp.run()
