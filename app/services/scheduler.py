"""FlowETL Background Scheduler Service.

Manages automated periodic and cron-like pipeline runs (seconds, minutes,
hourly, daily, weekly, monthly) using a pure-Python asyncio background worker.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from app.utils.logging import get_logger

logger = get_logger("flowetl.scheduler")

# Standard interval definitions in seconds
INTERVAL_MAP: Dict[str, int] = {
    "30s": 30,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
}


@dataclass
class ScheduledJob:
    """Represents a scheduled ETL pipeline job."""

    id: str
    name: str
    pipeline_name: str
    source_type: str
    source_options: Dict[str, Any]
    destination_type: str
    destination_options: Dict[str, Any]
    frequency: str  # '30s', '1m', 'hourly', 'daily', etc.
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    last_status: Optional[str] = None
    last_error: Optional[str] = None

    def calculate_next_run(self, from_time: Optional[datetime] = None) -> datetime:
        base = from_time or datetime.now()
        seconds = INTERVAL_MAP.get(self.frequency, 3600)
        return base + timedelta(seconds=seconds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pipeline_name": self.pipeline_name,
            "source_type": self.source_type,
            "source_options": self.source_options,
            "destination_type": self.destination_type,
            "destination_options": self.destination_options,
            "frequency": self.frequency,
            "transformations": self.transformations,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "last_status": self.last_status,
            "last_error": self.last_error,
        }


class SchedulerService:
    """Singleton scheduler orchestrator that drives periodic executions."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}
        self._runner_callback: Optional[Callable[..., str]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False

    def set_runner_callback(self, callback: Callable[..., str], loop: asyncio.AbstractEventLoop) -> None:
        self._runner_callback = callback
        self._loop = loop
        self.start()

    def start(self) -> None:
        if self._is_running or not self._loop:
            return
        self._is_running = True
        self._task = self._loop.create_task(self._worker_loop())
        logger.info("Scheduler service worker loop started.")

    def stop(self) -> None:
        self._is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Scheduler service worker loop stopped.")

    def add_schedule(
        self,
        name: str,
        pipeline_name: str,
        source_type: str,
        source_options: Dict[str, Any],
        destination_type: str,
        destination_options: Dict[str, Any],
        frequency: str = "hourly",
        transformations: Optional[List[Dict[str, Any]]] = None,
        is_enabled: bool = True,
    ) -> ScheduledJob:
        job_id = str(uuid.uuid4())[:8]
        job = ScheduledJob(
            id=job_id,
            name=name or f"Schedule-{job_id}",
            pipeline_name=pipeline_name,
            source_type=source_type,
            source_options=source_options,
            destination_type=destination_type,
            destination_options=destination_options,
            frequency=frequency,
            transformations=transformations or [],
            is_enabled=is_enabled,
        )
        job.next_run_at = job.calculate_next_run()
        self._jobs[job_id] = job
        logger.info("Added schedule '%s' (%s, next: %s)", job.name, job.frequency, job.next_run_at)
        return job

    def list_schedules(self) -> List[ScheduledJob]:
        return list(self._jobs.values())

    def get_schedule(self, job_id: str) -> Optional[ScheduledJob]:
        return self._jobs.get(job_id)

    def delete_schedule(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info("Deleted schedule '%s'", job_id)
            return True
        return False

    def toggle_schedule(self, job_id: str, enabled: Optional[bool] = None) -> Optional[ScheduledJob]:
        job = self.get_schedule(job_id)
        if not job:
            return None
        if enabled is None:
            job.is_enabled = not job.is_enabled
        else:
            job.is_enabled = enabled

        if job.is_enabled:
            job.next_run_at = job.calculate_next_run()
        else:
            job.next_run_at = None
        logger.info("Toggled schedule '%s': enabled=%s", job.name, job.is_enabled)
        return job

    def trigger_job(self, job_id: str) -> Optional[str]:
        """Manually trigger a scheduled job immediately."""
        job = self.get_schedule(job_id)
        if not job or not self._runner_callback or not self._loop:
            return None

        try:
            run_id = self._runner_callback(
                pipeline_name=f"[Scheduled] {job.pipeline_name}",
                source_type=job.source_type,
                source_options=job.source_options,
                destination_type=job.destination_type,
                destination_options=job.destination_options,
                loop=self._loop,
                transformations=job.transformations,
            )
            job.last_run_at = datetime.now()
            job.run_count += 1
            job.last_status = "triggered"
            if job.is_enabled:
                job.next_run_at = job.calculate_next_run()
            logger.info("Triggered schedule '%s' -> Run ID %s", job.name, run_id)
            return run_id
        except Exception as err:
            job.last_status = "error"
            job.last_error = str(err)
            logger.exception("Failed to trigger schedule '%s': %s", job.name, err)
            return None

    async def _worker_loop(self) -> None:
        """Background loop checking and executing due jobs every 2 seconds."""
        while self._is_running:
            try:
                now = datetime.now()
                for job in list(self._jobs.values()):
                    if job.is_enabled and job.next_run_at and now >= job.next_run_at:
                        logger.info("Schedule '%s' is due at %s. Triggering...", job.name, now)
                        self.trigger_job(job.id)
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error("Error in scheduler loop: %s", err)

            await asyncio.sleep(2)


# Module-level singleton
scheduler = SchedulerService()
