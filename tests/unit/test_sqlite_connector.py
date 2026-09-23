"""Unit tests for SQLite Relational Source and Destination Connectors."""

from pathlib import Path
import pytest

from app.connectors.base import ConnectorConfig
from app.connectors.registry import ConnectorRegistry
from app.connectors.sqlite import SQLiteDestination, SQLiteSource
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class TestSQLiteConnector:
    def test_registry_integration(self):
        assert ConnectorRegistry.get_source_class("sqlite") == SQLiteSource
        assert ConnectorRegistry.get_destination_class("sqlite") == SQLiteDestination

    def test_sqlite_ddl_and_crud(self, tmp_path: Path):
        db_file = tmp_path / "hospital.db"
        cfg = ConnectorConfig(
            name="sqlite_dest",
            connector_type="sqlite",
            options={"database": str(db_file)},
        )

        dest = SQLiteDestination(cfg)
        dest.connect()
        assert dest.test_connection() is True

        # Define Schema
        schema = TableSchema(
            name="patients",
            columns=[
                ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
                ColumnDefinition(name="full_name", data_type=DataType.STRING, nullable=False),
                ColumnDefinition(name="age", data_type=DataType.INTEGER),
                ColumnDefinition(name="is_active", data_type=DataType.BOOLEAN),
            ],
        )

        dest.create_schema(schema, if_exists="replace")

        # Load records
        rows = [
            {"id": 1, "full_name": "Alice Smith", "age": 30, "is_active": True},
            {"id": 2, "full_name": "Bob Jones", "age": 45, "is_active": False},
        ]
        inserted = dest.load(Dataset(schema=schema, rows=rows), "patients")
        assert inserted == 2
        dest.close()

        # Extract and verify schema discovery via SQLiteSource
        src = SQLiteSource(cfg)
        src.connect()
        assert src.test_connection() is True
        assert "patients" in src.list_tables()

        discovered = src.get_schema("patients")
        assert discovered.name == "patients"
        assert discovered.has_column("id")
        assert discovered.has_column("full_name")
        assert discovered.get_column("id").primary_key is True

        # Extract rows
        batches = list(src.extract("patients"))
        assert len(batches) == 1
        assert batches[0].row_count == 2
        assert batches[0].rows[0]["full_name"] == "Alice Smith"
        src.close()
