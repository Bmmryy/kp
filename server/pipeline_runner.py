"""PipelineRunner — background execution service for FlowETL pipelines.

Each pipeline run executes in a ThreadPoolExecutor so the FastAPI event loop
is never blocked. Progress events are pushed into a per-run asyncio.Queue and
consumed by the SSE endpoint.
"""
from __future__ import annotations

import asyncio
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import FlowETL core — triggers auto-registration of all connectors
import app.connectors  # noqa: F401
from app.connectors.base import ConnectorConfig
from app.connectors.registry import ConnectorRegistry
from app.core.pipeline import Pipeline
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR   = "error"


@dataclass
class PipelineRun:
    run_id: str
    pipeline_name: str
    source_type: str
    destination_type: str
    destination_options: Dict[str, Any] = field(default_factory=dict)
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    status: RunStatus = RunStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    log_lines: List[str] = field(default_factory=list)
    # Per-run SSE queue (asyncio-safe, set before thread starts)
    _event_queue: Optional[asyncio.Queue] = field(default=None, repr=False)
    _loop: Optional[asyncio.AbstractEventLoop] = field(default=None, repr=False)

    def push_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Thread-safe push of an SSE event into the async queue."""
        if self._loop and self._event_queue:
            payload = {"type": event_type, **data}
            self._loop.call_soon_threadsafe(self._event_queue.put_nowait, payload)

    def to_dict(self) -> Dict[str, Any]:
        output_file = None
        if self.destination_type in ("csv", "json", "jsonl", "sqlite"):
            output_file = self.destination_options.get("path") or self.destination_options.get("database")

        return {
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "source_type": self.source_type,
            "destination_type": self.destination_type,
            "destination_options": self.destination_options,
            "output_file": output_file,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "log_lines": self.log_lines[-200:],
        }


class PipelineRunnerService:
    """Singleton service managing all pipeline runs."""

    _instance: Optional["PipelineRunnerService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PipelineRunnerService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._runs: Dict[str, PipelineRun] = {}
                    instance._executor = ThreadPoolExecutor(
                        max_workers=4, thread_name_prefix="flowetl"
                    )
                    cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_registered_connectors(self) -> Dict[str, List[str]]:
        return {
            "sources": ConnectorRegistry.list_sources(),
            "destinations": ConnectorRegistry.list_destinations(),
        }

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        return self._runs.get(run_id)

    def list_runs(self) -> List[Dict[str, Any]]:
        runs = sorted(
            self._runs.values(),
            key=lambda r: r.started_at or datetime.min,
            reverse=True,
        )
        return [r.to_dict() for r in runs]

    def submit(
        self,
        pipeline_name: str,
        source_type: str,
        source_options: Dict[str, Any],
        destination_type: str,
        destination_options: Dict[str, Any],
        loop: asyncio.AbstractEventLoop,
        transformations: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Submit a pipeline for async execution. Returns run_id."""
        run_id = str(uuid.uuid4())[:8]
        run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            source_type=source_type,
            destination_type=destination_type,
            destination_options=destination_options,
            transformations=transformations or [],
        )
        run._loop = loop
        run._event_queue = asyncio.Queue()
        self._runs[run_id] = run

        self._executor.submit(
            self._execute,
            run,
            source_type,
            source_options,
            destination_type,
            destination_options,
            transformations or [],
        )
        return run_id

    # ------------------------------------------------------------------ #
    # Internal execution (runs in worker thread)                           #
    # ------------------------------------------------------------------ #

    def _execute(
        self,
        run: PipelineRun,
        source_type: str,
        source_options: Dict[str, Any],
        destination_type: str,
        destination_options: Dict[str, Any],
        transformations: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        run.status = RunStatus.RUNNING
        run.started_at = datetime.now()
        run.push_event("status", {"status": RunStatus.RUNNING.value, "message": "Pipeline dimulai..."})

        # Progress callback: signature (step: str, pct: float)
        def _progress(step: str, pct: float) -> None:
            pct_int = int(pct * 100)
            line = f"[{pct_int:3d}%] {step}"
            run.log_lines.append(line)
            run.push_event("progress", {
                "step": step,
                "percent": pct_int,
                "message": step,
                "log": line,
            })

        try:
            # Build connector instances via registry
            src_cfg = ConnectorConfig(
                name=f"src_{source_type}",
                connector_type=source_type,
                options=source_options,
            )
            dst_cfg = ConnectorConfig(
                name=f"dst_{destination_type}",
                connector_type=destination_type,
                options=destination_options,
            )
            source = ConnectorRegistry.create_source(src_cfg)
            destination = ConnectorRegistry.create_destination(dst_cfg)

            # Determine table names (optional in options; connector handles defaults)
            source_table = source_options.get("table_name") or source_options.get("table") or ""
            destination_table = destination_options.get("table_name") or destination_options.get("table") or source_table or "etl_output"

            # Build transformation objects
            built_transformers = []
            if transformations:
                import app.transformations  # noqa: F401
                from app.transformations.base import TransformerConfig
                from app.transformations.registry import TransformationRegistry
                for t_spec in transformations:
                    t_type = t_spec.get("type")
                    if t_type:
                        t_cfg = TransformerConfig(type=t_type, params=t_spec.get("params", {}))
                        built_transformers.append(TransformationRegistry.create(t_cfg))
                        logger.info("Attached transformer '%s' to pipeline '%s'", t_type, run.pipeline_name)

            pipeline = Pipeline(
                name=run.pipeline_name,
                source=source,
                destination=destination,
                source_table=source_table,
                destination_table=destination_table,
                transformations=built_transformers,
            )
            context = pipeline.run(progress_callback=_progress)

            if context.status.value in ("SUCCESS",):
                run.status = RunStatus.SUCCESS
                run.finished_at = datetime.now()
                run.metrics = {
                    "rows_extracted": context.metrics.rows_extracted,
                    "rows_transformed": context.metrics.rows_transformed,
                    "rows_loaded": context.metrics.rows_loaded,
                    "duration_seconds": round(context.metrics.duration_seconds, 4),
                }
                run.push_event("done", {"status": "success", "metrics": run.metrics})
            else:
                # Pipeline returned a FAILED context
                err_msg = "; ".join(e.get("message", "") for e in context.errors) or "Pipeline gagal."
                raise RuntimeError(err_msg)

        except Exception as exc:
            run.status = RunStatus.ERROR
            run.finished_at = datetime.now()
            run.error_message = str(exc)
            run.log_lines.append(f"[ERROR] {exc}")
            run.push_event("done", {"status": "error", "error": str(exc)})
            logger.exception("Pipeline run %s failed", run.run_id)

        finally:
            # Sentinel: tells SSE consumer the stream is done
            if run._loop and run._event_queue:
                run._loop.call_soon_threadsafe(run._event_queue.put_nowait, None)


# Module-level singleton
runner = PipelineRunnerService()
