"""Regression and verification tests for logic error fixes."""

import asyncio
from datetime import datetime
from pathlib import Path
import pytest

from app.core.exceptions import SchemaMappingError
from app.core.pipeline import Pipeline
from app.schema.casting import cast_value
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.services.scheduler import SchedulerService
from app.connectors.csv import CSVDestination
from app.connectors.base import ConnectorConfig


def test_invalid_boolean_string_raises():
    """Verify that invalid strings do NOT silently coerce to True."""
    with pytest.raises(SchemaMappingError):
        cast_value("tidak", DataType.BOOLEAN, column_name="is_active")

    with pytest.raises(SchemaMappingError):
        cast_value("salah", DataType.BOOLEAN, column_name="is_active")

    with pytest.raises(SchemaMappingError):
        cast_value("random_text", DataType.BOOLEAN, column_name="is_active")


def test_scheduler_advances_on_error():
    """Verify that scheduler advances next_run_at even when runner fails."""
    service = SchedulerService()

    def failing_runner(*args, **kwargs):
        raise RuntimeError("Database connection timed out!")

    class MockLoop:
        def create_task(self, coro):
            coro.close()
            return None

    service.set_runner_callback(failing_runner, MockLoop())
    job = service.add_schedule(
        name="Failing Job",
        pipeline_name="Fail Test",
        source_type="csv",
        source_options={},
        destination_type="json",
        destination_options={},
        frequency="1m",
    )

    old_next_run = job.next_run_at
    result = service.trigger_job(job.id)
    assert result is None
    assert job.last_status == "error"
    assert "Database connection timed out!" in job.last_error
    # next_run_at must advance into the future!
    assert job.next_run_at > old_next_run


def test_multi_batch_csv_replace_preserves_all_rows(tmp_path: Path):
    """Verify that multiple batches in replace mode do NOT overwrite previous batches."""
    csv_file = tmp_path / "multi_batch_out.csv"

    schema = TableSchema(
        name="test_table",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER),
            ColumnDefinition(name="val", data_type=DataType.STRING),
        ],
    )

    class MockSource:
        config = type("Config", (), {"name": "mock_src"})()
        def connect(self): pass
        def close(self): pass
        def extract(self, *args, **kwargs):
            # Yield 3 batches of 2 rows each
            yield Dataset(schema=schema, rows=[{"id": 1, "val": "a"}, {"id": 2, "val": "b"}])
            yield Dataset(schema=schema, rows=[{"id": 3, "val": "c"}, {"id": 4, "val": "d"}])
            yield Dataset(schema=schema, rows=[{"id": 5, "val": "e"}, {"id": 6, "val": "f"}])

    dest_cfg = ConnectorConfig(
        name="test_csv",
        connector_type="csv",
        options={"path": str(csv_file)},
    )
    dest = CSVDestination(dest_cfg)

    pipe = Pipeline(
        name="multi_batch_test",
        source=MockSource(),
        destination=dest,
        source_table="source",
        destination_table="target",
        load_mode="replace",
    )

    context = pipe.run()
    assert context.status.value == "SUCCESS"
    assert context.metrics.rows_loaded == 6

    # Read CSV contents to ensure all 6 rows are present (plus 1 header)
    lines = csv_file.read_text().strip().splitlines()
    assert len(lines) == 7  # 1 header + 6 data rows
    assert "5,e" in lines
    assert "1,a" in lines
