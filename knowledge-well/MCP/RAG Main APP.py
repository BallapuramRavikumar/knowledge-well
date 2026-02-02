from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys
import subprocess
import atexit

from .routers import health, ingest, query, chat, sparql

# Determine project root path
BASE_DIR = Path(__file__).resolve().parent.parent

# --- MCP Server Management ---
mcp_server_process = None

def start_mcp_server():
    """Starts the MCP server as a background process."""
    global mcp_server_process
    mcp_path = os.path.join(BASE_DIR, "mcp_server.py")
    if os.path.exists(mcp_path):
        mcp_server_process = subprocess.Popen([sys.executable, mcp_path], stdout=sys.stdout, stderr=sys.stderr)
        print("Started MCP server as a subprocess.")
    else:
        print(f"MCP server script not found at {mcp_path}")

def stop_mcp_server():
    """Stops the MCP server process."""
    global mcp_server_process
    if mcp_server_process:
        print("Terminating MCP server process...")
        mcp_server_process.terminate()
        mcp_server_process.wait()
        print("MCP server terminated.")

def create_app() -> FastAPI:
    app = FastAPI(title="GraphDB RAG API", version="0.1.0")

    # --- Routers ---
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(chat.router)
    app.include_router(sparql.router)

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Static files ---
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.mount("/js", StaticFiles(directory=str(BASE_DIR / "static" / "js")), name="js")

    # --- Serve HTML ---
    @app.get("/", response_class=FileResponse)
    async def serve_home():
        return FileResponse(BASE_DIR / "static" / "Knowledge_Well.html")

    # Start and stop the MCP server with the FastAPI app
    app.add_event_handler("startup", start_mcp_server)
    app.add_event_handler("shutdown", stop_mcp_server)
    atexit.register(stop_mcp_server) # Ensure cleanup on unexpected exit

    return app

app = create_app()
