"""REST API endpoints for FlowETL pipeline management."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.pipeline_runner import runner

router = APIRouter(prefix="/api", tags=["pipelines"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RunPipelineRequest(BaseModel):
    pipeline_name: str = Field(default="Unnamed Pipeline", description="Nama pipeline")
    source_type: str = Field(..., description="Jenis source connector (csv, sqlite, mysql, ...)")
    source_options: Dict[str, Any] = Field(default_factory=dict)
    destination_type: str = Field(..., description="Jenis destination connector")
    destination_options: Dict[str, Any] = Field(default_factory=dict)


class RunPipelineResponse(BaseModel):
    run_id: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/connectors")
def list_connectors() -> Dict[str, List[str]]:
    """Kembalikan semua connector types yang terdaftar."""
    return runner.get_registered_connectors()


@router.post("/pipeline/run", response_model=RunPipelineResponse)
async def run_pipeline(request: Request, body: RunPipelineRequest) -> RunPipelineResponse:
    """Submit pipeline untuk dijalankan di background thread."""
    loop = asyncio.get_event_loop()
    run_id = runner.submit(
        pipeline_name=body.pipeline_name,
        source_type=body.source_type,
        source_options=body.source_options,
        destination_type=body.destination_type,
        destination_options=body.destination_options,
        loop=loop,
    )
    return RunPipelineResponse(run_id=run_id, message=f"Pipeline '{body.pipeline_name}' dikirim. run_id={run_id}")


@router.get("/pipeline/status/{run_id}")
def get_status(run_id: str) -> Dict[str, Any]:
    """Cek status satu pipeline run."""
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run ID '{run_id}' tidak ditemukan.")
    return run.to_dict()


@router.get("/pipeline/history")
def list_history() -> List[Dict[str, Any]]:
    """Daftar semua pipeline runs (terbaru di atas)."""
    return runner.list_runs()


@router.get("/stream/{run_id}")
async def stream_progress(run_id: str) -> StreamingResponse:
    """Server-Sent Events stream untuk real-time progress dari satu run."""
    run = runner.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run ID '{run_id}' tidak ditemukan.")

    async def event_generator():
        # Kirim log yang sudah ada dulu (jika reconnect)
        for line in run.log_lines:
            yield f"data: {line}\n\n"

        # Streaming events baru
        queue = run._event_queue
        if queue is None:
            return

        import json
        while True:
            event = await queue.get()
            if event is None:  # sentinel — stream selesai
                yield "event: close\ndata: done\n\n"
                break
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
