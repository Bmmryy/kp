"""FlowETL Web Server — FastAPI application factory."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.api.pipelines import router as pipeline_router
from server.api.schedules import router as schedules_router
from server.pipeline_runner import runner
from app.services.scheduler import scheduler

BASE_DIR = Path(__file__).parent

app = FastAPI(
    title="FlowETL",
    description="Generic Visual ETL / Data Integration Tool",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

@app.middleware("http")
async def no_cache_middleware(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# API routes
app.include_router(pipeline_router)
app.include_router(schedules_router)


@app.on_event("startup")
async def startup_event():
    """Start the background scheduler with the active asyncio loop."""
    loop = asyncio.get_event_loop()
    scheduler.set_runner_callback(runner.submit, loop)


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    """Serve the single-page application shell."""
    return FileResponse(
        str(BASE_DIR / "templates" / "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "FlowETL"}


from server.api.pipelines import stream_progress

@app.get("/stream/{run_id}")
async def root_stream(run_id: str):
    """Direct alias for /api/stream/{run_id}."""
    return await stream_progress(run_id)

