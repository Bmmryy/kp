"""REST API endpoints for FlowETL automated pipeline scheduling."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scheduler import scheduler

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class CreateScheduleRequest(BaseModel):
    name: str = Field(default="My Schedule", description="Nama jadwal")
    pipeline_name: str = Field(default="Scheduled Pipeline", description="Nama pipeline yang dijalankan")
    source_type: str = Field(..., description="Tipe source (mysql, sqlite, csv, ...)")
    source_options: Dict[str, Any] = Field(default_factory=dict)
    destination_type: Optional[str] = Field(default=None, description="Tipe destination")
    dest_type: Optional[str] = Field(default=None, description="Alias untuk destination_type")
    destination_options: Dict[str, Any] = Field(default_factory=dict)
    dest_options: Dict[str, Any] = Field(default_factory=dict)
    frequency: str = Field(default="hourly", description="'30s', '1m', '5m', 'hourly', 'daily', 'weekly', 'monthly'")
    transformations: List[Dict[str, Any]] = Field(default_factory=list)
    is_enabled: bool = Field(default=True)

    @property
    def effective_destination_type(self) -> str:
        return self.destination_type or self.dest_type or "csv"

    @property
    def effective_destination_options(self) -> Dict[str, Any]:
        return self.destination_options or self.dest_options or {}


class ScheduleResponse(BaseModel):
    id: str
    message: str


@router.get("")
def list_schedules() -> List[Dict[str, Any]]:
    """Kembalikan semua daftar jadwal ETL."""
    return [job.to_dict() for job in scheduler.list_schedules()]


@router.post("", response_model=ScheduleResponse)
def create_schedule(body: CreateScheduleRequest) -> ScheduleResponse:
    """Buat jadwal pipeline baru."""
    job = scheduler.add_schedule(
        name=body.name,
        pipeline_name=body.pipeline_name,
        source_type=body.source_type,
        source_options=body.source_options,
        destination_type=body.effective_destination_type,
        destination_options=body.effective_destination_options,
        frequency=body.frequency,
        transformations=body.transformations,
        is_enabled=body.is_enabled,
    )
    return ScheduleResponse(id=job.id, message=f"Jadwal '{job.name}' berhasil dibuat ({job.frequency}).")


@router.get("/{job_id}")
def get_schedule(job_id: str) -> Dict[str, Any]:
    """Ambil detail satu jadwal berdasarkan ID."""
    job = scheduler.get_schedule(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
    return job.to_dict()


@router.put("/{job_id}")
def update_schedule(job_id: str, body: CreateScheduleRequest) -> Dict[str, Any]:
    """Update jadwal yang sudah ada."""
    job = scheduler.update_schedule(
        job_id=job_id,
        name=body.name,
        pipeline_name=body.pipeline_name,
        source_type=body.source_type,
        source_options=body.source_options,
        destination_type=body.effective_destination_type,
        destination_options=body.effective_destination_options,
        frequency=body.frequency,
        transformations=body.transformations,
        is_enabled=body.is_enabled,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
    return job.to_dict()


@router.delete("/{job_id}")
def delete_schedule(job_id: str) -> Dict[str, Any]:
    """Hapus satu jadwal."""
    success = scheduler.delete_schedule(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
    return {"status": "ok", "message": f"Jadwal '{job_id}' telah dihapus."}


@router.patch("/{job_id}/toggle")
def toggle_schedule(job_id: str) -> Dict[str, Any]:
    """Nyalakan atau matikan jadwal (Toggle On/Off)."""
    job = scheduler.toggle_schedule(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
    status_str = "aktif" if job.is_enabled else "nonaktif"
    return {"status": "ok", "is_enabled": job.is_enabled, "message": f"Jadwal '{job.name}' sekarang {status_str}."}


@router.post("/{job_id}/trigger")
def trigger_now(job_id: str) -> Dict[str, Any]:
    """Jalankan jadwal secara instan sekarang."""
    run_id = scheduler.trigger_job(job_id)
    if not run_id:
        raise HTTPException(status_code=400, detail="Gagal menjalankan jadwal.")
    return {"status": "ok", "run_id": run_id, "message": f"Jadwal dijalankan langsung! run_id={run_id}"}
