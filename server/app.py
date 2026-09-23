"""FlowETL Web Server — FastAPI application factory."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.api.pipelines import router as pipeline_router

BASE_DIR = Path(__file__).parent

app = FastAPI(
    title="FlowETL",
    description="Generic Visual ETL / Data Integration Tool",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# API routes
app.include_router(pipeline_router)


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    """Serve the single-page application shell."""
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "FlowETL"}
