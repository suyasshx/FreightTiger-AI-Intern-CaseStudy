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

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "RouteGuard AI - Freight Cost Intelligence Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
