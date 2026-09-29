"""REST API endpoints for FlowETL pipeline management."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.pipeline_runner import runner, RunStatus

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
        import json

        # Jika pipeline sudah selesai sebelum stream tersambung
        if run.status in (RunStatus.SUCCESS, RunStatus.ERROR):
            for line in run.log_lines:
                yield f"event: progress\ndata: {json.dumps({'log': line, 'percent': 100 if run.status == RunStatus.SUCCESS else 0, 'step': 'DONE', 'message': line})}\n\n"
            done_payload = {
                "status": run.status.value,
                "metrics": run.metrics,
                "error": run.error_message,
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
            yield "event: close\ndata: done\n\n"
            return

        # Kirim log yang sudah ada dulu (jika reconnect)
        for line in run.log_lines:
            yield f"event: progress\ndata: {json.dumps({'log': line, 'percent': 50, 'step': 'RUNNING', 'message': line})}\n\n"

        # Streaming events baru dari queue
        queue = run._event_queue
        if queue is None:
            return

        while True:
            event = await queue.get()
            if event is None:  # sentinel — stream selesai
                # Kirim status akhir jika belum terkirim
                if run.status in (RunStatus.SUCCESS, RunStatus.ERROR):
                    done_payload = {
                        "status": run.status.value,
                        "metrics": run.metrics,
                        "error": run.error_message,
                    }
                    yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
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


# ---------------------------------------------------------------------------
# File Download & Management Endpoints
# ---------------------------------------------------------------------------

from pathlib import Path
from fastapi.responses import FileResponse

DATA_DIR = Path("data")


@router.get("/files")
def list_exported_files() -> List[Dict[str, Any]]:
    """Daftar semua file hasil export di direktori data/."""
    files_list = []
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check data/ folder and output/ folder
    search_dirs = [DATA_DIR, Path("output"), Path(".")]
    seen = set()

    for directory in search_dirs:
        if not directory.exists():
            continue
        for p in directory.glob("*.*"):
            if p.suffix.lower() in (".csv", ".json", ".jsonl", ".sqlite", ".db") and p.name not in seen:
                if p.name.startswith("."):
                    continue
                seen.add(p.name)
                stat = p.stat()
                files_list.append({
                    "name": p.name,
                    "path": str(p),
                    "size_bytes": stat.st_size,
                    "size_formatted": f"{stat.st_size / 1024:.1f} KB" if stat.st_size >= 1024 else f"{stat.st_size} B",
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "download_url": f"/api/files/download?path={p}",
                })

    files_list.sort(key=lambda x: x["modified"], reverse=True)
    return files_list


@router.get("/files/download")
def download_file(path: str) -> FileResponse:
    """Download file hasil export."""
    target_path = Path(path).resolve()
    base_dir = Path(".").resolve()

    # Prevent path traversal outside project workspace
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Akses ditolak.")

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{path}' tidak ditemukan.")

    return FileResponse(
        path=str(target_path),
        filename=target_path.name,
        media_type="application/octet-stream",
    )


@router.post("/database/install-sql")
def install_hospital_sql() -> Dict[str, Any]:
    """Install / re-import Hospital_Management_System.sql secara otomatis."""
    import subprocess
    sql_path = Path("/tmp/hospital_v3.sql")
    if not sql_path.exists():
        sql_path = Path("/Users/ghn/.gemini/antigravity/brain/1c06a422-44e4-4627-b23e-92f843b079bf/scratch/hospital_mysql.sql")

    if not sql_path.exists():
        raise HTTPException(status_code=404, detail="File SQL konversi tidak ditemukan.")

    cmd = ["mysql", "-u", "root", "--force"]
    with open(sql_path, "r", encoding="utf-8") as f:
        res = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=120)

    # Get row counts
    count_cmd = ["mysql", "-u", "root", "HospitalManagementSystem", "-e", "SHOW TABLES;"]
    verify = subprocess.run(count_cmd, capture_output=True, text=True, timeout=10)
    tables = [l for l in verify.stdout.split("\n") if l and "Tables_in" not in l]

    return {
        "status": "success",
        "message": f"Database HospitalManagementSystem berhasil di-install! Total {len(tables)} tabel siap digunakan.",
        "tables": tables,
    }

