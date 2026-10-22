"""Unit tests for Excel (XLSX) Source and Destination Connectors."""

from pathlib import Path
import pytest

from app.connectors.base import ConnectorConfig
from app.connectors.excel import ExcelDestination, ExcelSource
from app.connectors.registry import ConnectorRegistry
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


def test_excel_connector_registration():
    """Verify excel and xlsx are registered in ConnectorRegistry."""
    import app.connectors
    assert "excel" in ConnectorRegistry.list_sources()
    assert "excel" in ConnectorRegistry.list_destinations()
    assert "xlsx" in ConnectorRegistry.list_sources()
    assert "xlsx" in ConnectorRegistry.list_destinations()


def test_excel_write_and_read(tmp_path: Path):
    """Test full cycle write and read with openpyxl Excel connector."""
    xlsx_path = tmp_path / "test_out.xlsx"
    schema = TableSchema(
        name="test_table",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="score", data_type=DataType.FLOAT),
        ]
    )
    rows = [
        {"id": 1, "name": "Budi", "score": 88.5},
        {"id": 2, "name": "Siti", "score": 95.0},
    ]
    ds = Dataset(schema=schema, rows=rows)

    cfg = ConnectorConfig(name="test_dst", connector_type="excel", options={"path": str(xlsx_path)})
    dst = ExcelDestination(cfg)
    dst.connect()
    dst.create_schema(schema, if_exists="replace")
    loaded = dst.load(ds, "test_table")
    assert loaded == 2
    assert xlsx_path.exists()

    # Read back
    src_cfg = ConnectorConfig(name="test_src", connector_type="excel", options={"path": str(xlsx_path)})
    src = ExcelSource(src_cfg)
    src.connect()
    tables = src.list_tables()
    assert "test_table" in tables

    read_schema = src.get_schema("test_table")
    assert [c.name for c in read_schema.columns] == ["id", "name", "score"]

    batches = list(src.extract("test_table"))
    assert len(batches) == 1
    assert len(batches[0].rows) == 2
    assert batches[0].rows[0]["id"] == 1
    assert batches[0].rows[0]["name"] == "Budi"
    assert batches[0].rows[1]["score"] == 95.0
