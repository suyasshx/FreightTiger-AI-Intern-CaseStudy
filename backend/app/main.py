"""
RouteGuard AI - Main FastAPI Application Server
Provides RESTful backend services for the RouteGuard AI freight intelligence dashboard.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.services.pipeline import run_pipeline, pipeline_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: execute baseline pipeline to populate in-memory state and ChromaDB
    print("[RouteGuard AI] Initializing pipeline on server startup...")
    try:
        run_pipeline()
        print(f"[RouteGuard AI] Startup complete: {len(pipeline_state.records)} route-weeks loaded.")
    except Exception as e:
        print(f"[RouteGuard AI Error] Startup pipeline execution failed: {e}")
    yield


app = FastAPI(
    title="RouteGuard AI API",
    description="Evidence-Grounded Freight Cost Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite dev server and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

app.include_router(router)

# Mount compiled React frontend if present
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "message": "Welcome to RouteGuard AI API",
            "docs": "/docs",
            "health": "/api/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
