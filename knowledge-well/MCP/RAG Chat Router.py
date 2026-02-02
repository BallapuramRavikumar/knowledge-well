from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import time
import subprocess
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel
from langchain_core.pydantic_v1 import Field
from langchain_openai import ChatOpenAI
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache

from ..core.config import settings


# A minimal pydantic model to define our tool's input
class RAGToolInput(LangChainBaseModel):
    question: str = Field(..., description="The user's question to be answered.")
    k: Optional[int] = Field(5, description="The number of documents to retrieve from the vector store.")
    temperature: Optional[float] = Field(0.2, description="The temperature for the language model.")


# This is a placeholder, as the actual tool is loaded from the MCP server
class RAGTool:
    name: str = "chat_rag"
    description: str = "Answers questions by retrieving information from a knowledge graph and a vector store."
    args_schema: BaseModel = RAGToolInput
    func: callable


router = APIRouter()
set_llm_cache(InMemoryCache())


@router.post("/chat")
def chat(req: RAGToolInput):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")

    async def invoke_agent():
        # Start the MCP server as a subprocess and connect to it
        mcp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mcp_server.py")
        server_params = StdioServerParameters("python", [mcp_path])

        async with stdio_client(server_params) as client:
            mcp_tools = await load_mcp_tools(client)

            # Create a ReAct agent to use the MCP tools
            llm_provider = settings.LLM_PROVIDER.upper()
            if llm_provider == "OPENAI":
                llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
            else:
                # Fallback to Ollama or other local models
                llm = ChatOpenAI(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)

            prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad"],
                template="""
                You are a helpful and precise assistant. Use the provided tools to answer the user's question.

                TOOLS:
                {tools}

                USER'S QUESTION:
                {input}

                {agent_scratchpad}
                """
            )

            agent = create_react_agent(llm, mcp_tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=mcp_tools, verbose=True)

            response = await agent_executor.ainvoke({"input": req.question})
            return response['output']

    t0 = time.perf_counter()
    answer = asyncio.run(invoke_agent())
    total_ms = (time.perf_counter() - t0) * 1000

    return {
        "answer": answer,
        "timing": {
            "total_ms": round(total_ms, 1),
        },
    }
