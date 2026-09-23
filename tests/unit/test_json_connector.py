"""Unit tests for JSON & JSON Lines Source and Destination Connectors."""

from pathlib import Path
import pytest

from app.connectors.base import ConnectorConfig
from app.connectors.json import JSONDestination, JSONSource
from app.connectors.registry import ConnectorRegistry
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class TestJSONConnector:
    def test_registry_integration(self):
        assert ConnectorRegistry.get_source_class("json") == JSONSource
        assert ConnectorRegistry.get_destination_class("json") == JSONDestination
        assert ConnectorRegistry.get_source_class("jsonl") == JSONSource
        assert ConnectorRegistry.get_destination_class("jsonl") == JSONDestination

    def test_json_array_write_and_read(self, tmp_path: Path):
        json_file = tmp_path / "hospital_data.json"
        dest = JSONDestination(
            ConnectorConfig(
                name="json_dest",
                connector_type="json",
                options={"path": str(json_file)},
            )
        )
        dest.connect()

        schema = TableSchema(
            name="hospital_data",
            columns=[
                ColumnDefinition(name="id", data_type=DataType.INTEGER),
                ColumnDefinition(name="department", data_type=DataType.STRING),
            ],
        )
        dest.create_schema(schema, if_exists="replace")

        rows = [
            {"id": 1, "department": "Cardiology"},
            {"id": 2, "department": "Neurology"},
        ]
        dest.load(Dataset(schema=schema, rows=rows), "hospital_data", mode="append")
        dest.close()

        # Read back
        source = JSONSource(
            ConnectorConfig(
                name="json_src",
                connector_type="json",
                options={"path": str(json_file)},
            )
        )
        source.connect()
        discovered_schema = source.get_schema("hospital_data")
        assert discovered_schema.has_column("department")

        batches = list(source.extract("hospital_data"))
        assert len(batches) == 1
        assert batches[0].row_count == 2
        assert batches[0].rows[1]["department"] == "Neurology"
        source.close()

    def test_json_lines_write_and_read(self, tmp_path: Path):
        jsonl_file = tmp_path / "events.jsonl"
        dest = JSONDestination(
            ConnectorConfig(
                name="jsonl_dest",
                connector_type="jsonl",
                options={"path": str(jsonl_file), "lines": True},
            )
        )
        dest.connect()
        schema = TableSchema(
            name="events",
            columns=[ColumnDefinition(name="event_id", data_type=DataType.INTEGER)],
        )
        dest.load(Dataset(schema=schema, rows=[{"event_id": 10}, {"event_id": 20}]), "events")
        dest.close()

        source = JSONSource(
            ConnectorConfig(
                name="jsonl_src",
                connector_type="jsonl",
                options={"path": str(jsonl_file), "lines": True},
            )
        )
        source.connect()
        batches = list(source.extract("events", chunk_size=1))
        assert len(batches) == 2
        assert batches[0].rows[0]["event_id"] == 10
        source.close()
