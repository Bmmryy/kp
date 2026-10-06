"""Pipeline Orchestrator for FlowETL.

Coordinates the end-to-end Extract-Transform-Load execution lifecycle,
tracking metrics, managing connector sessions, invoking transformations,
and updating execution context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional
import time

if TYPE_CHECKING:
    from app.connectors.base import DestinationConnector, SourceConnector
    from app.transformations.base import Transformer

from app.core.context import PipelineContext, PipelineRunStatus
from app.core.exceptions import (
    ExtractionError,
    FlowETLError,
    LoadError,
    PipelineExecutionError,
    TransformationError,
)
from app.schema.models import Dataset
from app.utils.logging import get_logger

logger = get_logger("flowetl.pipeline")


class Pipeline:
    """Core execution engine for a FlowETL data integration pipeline."""

    def __init__(
        self,
        name: str,
        source: SourceConnector,
        destination: DestinationConnector,
        source_table: str,
        destination_table: str,
        transformations: Optional[List[Transformer]] = None,
        load_mode: str = "append",
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> None:
        self.name = name
        self.source = source
        self.destination = destination
        self.source_table = source_table
        self.destination_table = destination_table
        self.transformations = transformations or []
        self.load_mode = load_mode
        self.query = query
        self.chunk_size = chunk_size

    def run(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> PipelineContext:
        """Executes the pipeline lifecycle and returns the execution context."""
        context = PipelineContext(
            pipeline_name=self.name,
            source_name=self.source.config.name,
            destination_name=self.destination.config.name,
        )

        def report_step(step_name: str, progress: float) -> None:
            context.current_step = step_name
            context.add_log(f"Step {step_name} started (progress: {int(progress * 100)}%)")
            logger.info(f"[{self.name}] Step: {step_name} ({int(progress * 100)}%)")
            if progress_callback:
                progress_callback(step_name, progress)

        context.mark_started()
        logger.info(f"[{self.name}] Pipeline execution started (Run ID: {context.run_id})")

        try:
            # 1. Connect Phase
            report_step("CONNECTING_SOURCE", 0.1)
            self.source.connect()
            logger.info(f"[{self.name}] Source connected successfully")

            report_step("CONNECTING_DESTINATION", 0.2)
            self.destination.connect()
            logger.info(f"[{self.name}] Destination connected successfully")

            # 2. Extract Phase
            report_step("EXTRACTING", 0.3)
            extracted_datasets: List[Dataset] = []
            for batch in self.source.extract(
                table_name=self.source_table,
                query=self.query,
                chunk_size=self.chunk_size,
            ):
                context.metrics.rows_extracted += batch.row_count
                extracted_datasets.append(batch)

            logger.info(f"[{self.name}] Extracted {context.metrics.rows_extracted} rows")

            # 3. Transform Phase
            report_step("TRANSFORMING", 0.6)
            transformed_datasets: List[Dataset] = []
            for dataset in extracted_datasets:
                current = dataset
                for transformer in self.transformations:
                    try:
                        current = transformer.transform(current)
                    except Exception as err:
                        raise TransformationError(
                            f"Transformation '{transformer.config.type}' failed: {err}",
                            details=str(err),
                            suggested_action="Review transformation inputs and rules.",
                        ) from err
                transformed_datasets.append(current)
                context.metrics.rows_transformed += current.row_count

            logger.info(f"[{self.name}] Transformed {context.metrics.rows_transformed} rows")

            # 4. Load Phase
            report_step("LOADING", 0.85)
            # Ensure destination target schema is prepared if we have at least one batch
            if transformed_datasets:
                first_batch = transformed_datasets[0]
                dest_schema = first_batch.schema_def
                if self.destination_table and dest_schema.name != self.destination_table:
                    dest_schema = dest_schema.model_copy(update={"name": self.destination_table})

                self.destination.create_schema(
                    schema=dest_schema,
                    if_exists=self.load_mode,
                )

                for batch in transformed_datasets:
                    rows_loaded = self.destination.load(
                        dataset=batch,
                        table_name=self.destination_table,
                        mode=self.load_mode,
                    )
                    context.metrics.rows_loaded += rows_loaded

            logger.info(f"[{self.name}] Loaded {context.metrics.rows_loaded} rows")

            # 5. Success
            context.mark_success()
            report_step("COMPLETED", 1.0)
            logger.info(
                f"[{self.name}] Pipeline completed successfully in {context.metrics.duration_seconds}s"
            )

        except FlowETLError as etl_err:
            logger.error(f"[{self.name}] Pipeline failed: {etl_err.to_user_friendly_string()}")
            context.mark_failed(etl_err.message, details=etl_err.details)
            if etl_err.suggested_action:
                context.add_warning(f"Suggestion: {etl_err.suggested_action}")
        except Exception as unexpected_err:
            logger.exception(f"[{self.name}] Unexpected error occurred")
            context.mark_failed(
                f"Unexpected runtime error: {unexpected_err}",
                details=str(unexpected_err),
            )
        finally:
            try:
                self.source.close()
            except Exception:
                pass
            try:
                self.destination.close()
            except Exception:
                pass

        return context
