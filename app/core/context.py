"""Pipeline Execution Context & Observability Models for FlowETL."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class PipelineRunStatus(str, Enum):
    """Execution status lifecycle states for a pipeline run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PipelineMetrics(BaseModel):
    """Quantitative performance and throughput metrics for a run."""

    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    rows_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    def start(self) -> None:
        self.start_time = datetime.now(timezone.utc)

    def finish(self) -> None:
        self.end_time = datetime.now(timezone.utc)
        if self.start_time:
            self.duration_seconds = round(
                (self.end_time - self.start_time).total_seconds(), 4
            )


class PipelineContext(BaseModel):
    """Full execution context and state tracker for a single pipeline run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    pipeline_name: str = Field(..., description="Name of executing pipeline")
    source_name: str = Field(default="", description="Source connector identifier")
    destination_name: str = Field(default="", description="Destination connector identifier")
    status: PipelineRunStatus = Field(default=PipelineRunStatus.PENDING)
    metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)
    logs: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    current_step: str = Field(default="INITIALIZED")

    def add_log(self, message: str) -> None:
        self.logs.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def mark_started(self) -> None:
        self.status = PipelineRunStatus.RUNNING
        self.metrics.start()
        self.current_step = "EXTRACTING"

    def mark_success(self) -> None:
        self.status = PipelineRunStatus.SUCCESS
        self.current_step = "COMPLETED"
        self.metrics.finish()

    def mark_failed(self, error_message: str, details: Optional[str] = None) -> None:
        self.status = PipelineRunStatus.FAILED
        self.current_step = "FAILED"
        self.errors.append({"message": error_message, "details": details})
        self.metrics.finish()
