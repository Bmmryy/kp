"""Unit tests for minimal pipeline orchestrator, context, and metrics."""

from typing import Iterator, List, Optional
import pytest

from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.context import PipelineRunStatus
from app.core.pipeline import Pipeline
from app.schema.models import Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig


class MockSource(SourceConnector):
    """In-memory mock source connector for testing pipeline orchestration."""

    def __init__(self, config: ConnectorConfig, dataset: Dataset) -> None:
        super().__init__(config)
        self.mock_dataset = dataset

    def connect(self) -> None:
        self._is_connected = True

    def test_connection(self) -> bool:
        return True

    def list_tables(self) -> List[str]:
        return [self.mock_dataset.schema_def.name]

    def get_schema(self, table_name: str) -> TableSchema:
        return self.mock_dataset.schema_def

    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        yield self.mock_dataset

    def close(self) -> None:
        self._is_connected = False


class MockDestination(DestinationConnector):
    """In-memory mock destination connector for verifying load behavior."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.created_schemas: List[TableSchema] = []
        self.loaded_records: List[dict] = []

    def connect(self) -> None:
        self._is_connected = True

    def test_connection(self) -> bool:
        return True

    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        self.created_schemas.append(schema)

    def load(self, dataset: Dataset, table_name: str, mode: str = "append") -> int:
        self.loaded_records.extend(dataset.rows)
        return len(dataset.rows)

    def close(self) -> None:
        self._is_connected = False


class SimpleUppercaseTransformer(Transformer):
    """Sample transformer that uppercases a specified column."""

    def transform(self, dataset: Dataset) -> Dataset:
        target_col = self.config.params.get("column", "name")
        transformed_rows = []
        for r in dataset.rows:
            new_r = dict(r)
            if target_col in new_r and isinstance(new_r[target_col], str):
                new_r[target_col] = new_r[target_col].upper()
            transformed_rows.append(new_r)
        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


def test_pipeline_successful_execution(sample_dataset):
    source_cfg = ConnectorConfig(name="mock_src", connector_type="mock")
    dest_cfg = ConnectorConfig(name="mock_dest", connector_type="mock")

    source = MockSource(source_cfg, sample_dataset)
    destination = MockDestination(dest_cfg)
    transformer = SimpleUppercaseTransformer(
        TransformerConfig(type="uppercase", params={"column": "name"})
    )

    pipeline = Pipeline(
        name="test_hospital_pipeline",
        source=source,
        destination=destination,
        source_table="patients",
        destination_table="patients_clean",
        transformations=[transformer],
    )

    context = pipeline.run()

    assert context.status == PipelineRunStatus.SUCCESS
    assert context.metrics.rows_extracted == 3
    assert context.metrics.rows_transformed == 3
    assert context.metrics.rows_loaded == 3
    assert context.metrics.rows_failed == 0
    assert context.metrics.duration_seconds >= 0.0

    # Verify transformed contents
    assert len(destination.loaded_records) == 3
    assert destination.loaded_records[0]["name"] == "ALICE SMITH"
    assert destination.loaded_records[1]["name"] == "BOB JONES"

    # Verify connectors closed
    assert not source.is_connected
    assert not destination.is_connected


def test_pipeline_progress_callback(sample_dataset):
    source_cfg = ConnectorConfig(name="mock_src", connector_type="mock")
    dest_cfg = ConnectorConfig(name="mock_dest", connector_type="mock")
    source = MockSource(source_cfg, sample_dataset)
    destination = MockDestination(dest_cfg)

    steps_recorded = []

    def on_progress(step: str, pct: float):
        steps_recorded.append((step, pct))

    pipeline = Pipeline(
        name="callback_pipeline",
        source=source,
        destination=destination,
        source_table="patients",
        destination_table="patients",
    )

    context = pipeline.run(progress_callback=on_progress)
    assert context.status == PipelineRunStatus.SUCCESS
    assert len(steps_recorded) > 0
    assert any(s[0] == "COMPLETED" for s in steps_recorded)
