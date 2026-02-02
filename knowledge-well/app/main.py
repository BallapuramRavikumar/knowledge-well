from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routers import health, ingest, query, chat, sparql

# ← add sparql

BASE_DIR = Path(__file__).resolve().parent.parent  # root folder of your project

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
        allow_origins=["*"],  # dev-friendly; restrict in prod
        allow_methods=["*"],
        allow_headers=["*"],

    )

    # --- Static files (optional if you have css/js) ---
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.mount("/js", StaticFiles(directory=str(BASE_DIR / "static" / "js")), name="js")

    # --- Serve HTML ---
    @app.get("/", response_class=FileResponse)
    async def serve_home():
        return FileResponse(BASE_DIR / "static" / "Knowledge_Well.html")
        # return FileResponse(BASE_DIR / "static" / "Knowledge_Well_Local.html")


    return app


app = create_app()
