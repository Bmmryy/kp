"""Unit tests for CSV Source and Destination Connectors."""

from pathlib import Path
import pytest

from app.connectors.base import ConnectorConfig
from app.connectors.csv import CSVDestination, CSVSource
from app.connectors.registry import ConnectorRegistry
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class TestCSVConnector:
    def test_registry_integration(self):
        source_cls = ConnectorRegistry.get_source_class("csv")
        dest_cls = ConnectorRegistry.get_destination_class("csv")
        assert source_cls == CSVSource
        assert dest_cls == CSVDestination

    def test_csv_write_and_read(self, tmp_path: Path):
        csv_file = tmp_path / "patients.csv"
        dest_config = ConnectorConfig(
            name="test_csv_dest",
            connector_type="csv",
            options={"path": str(csv_file)},
        )
        dest = CSVDestination(dest_config)
        dest.connect()

        schema = TableSchema(
            name="patients",
            columns=[
                ColumnDefinition(name="patient_id", data_type=DataType.INTEGER, primary_key=True),
                ColumnDefinition(name="name", data_type=DataType.STRING),
                ColumnDefinition(name="age", data_type=DataType.INTEGER),
            ],
        )
        dest.create_schema(schema, if_exists="replace")

        records = [
            {"patient_id": 101, "name": "Alice Wonderland", "age": 29},
            {"patient_id": 102, "name": "Bob Marley", "age": 45},
            {"patient_id": 103, "name": "Charlie Brown", "age": 15},
        ]
        dataset = Dataset(schema=schema, rows=records)
        loaded_count = dest.load(dataset, "patients", mode="append")
        assert loaded_count == 3
        dest.close()

        # Read back via CSVSource
        src_config = ConnectorConfig(
            name="test_csv_src",
            connector_type="csv",
            options={"path": str(csv_file)},
        )
        source = CSVSource(src_config)
        source.connect()
        assert source.test_connection() is True

        discovered_schema = source.get_schema("patients")
        assert discovered_schema.has_column("patient_id")
        assert discovered_schema.has_column("name")
        assert discovered_schema.has_column("age")

        # Extract in chunk sizes of 2
        batches = list(source.extract("patients", chunk_size=2))
        assert len(batches) == 2
        assert batches[0].row_count == 2
        assert batches[1].row_count == 1
        assert batches[0].rows[0]["name"] == "Alice Wonderland"
        source.close()
