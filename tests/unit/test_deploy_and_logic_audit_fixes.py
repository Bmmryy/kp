"""Comprehensive Unit Tests for Deployment & Logic Audit Fixes."""

import os
import tempfile
import sqlite3
import pytest
from datetime import datetime, date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.connectors.base import ConnectorConfig
from app.connectors.sql_base import SQLBaseDestination
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import TransformerConfig
from app.transformations.registry import TransformationRegistry
from server.app import app
from server.pipeline_runner import runner


class MockSQLiteSQLBaseDestination(SQLBaseDestination):
    """Concrete subclass of SQLBaseDestination using SQLite to test sql_base logic."""

    @property
    def dialect(self) -> str:
        return "sqlite"

    def _build_url(self) -> str:
        return f"sqlite:///{self.config.options['database']}"

    def _quote_identifier(self, name: str) -> str:
        escaped = name.replace('"', '""')
        return f'"{escaped}"'


def test_fix_sql_base_destination_column_names_with_spaces():
    """Verify that SQLBaseDestination safely loads rows into columns with spaces using indexed params."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        cfg = ConnectorConfig(
            name="test_dst",
            connector_type="sql_base_test",
            options={"database": db_path},
        )
        dest = MockSQLiteSQLBaseDestination(cfg)

        schema = TableSchema(
            name="orders_report",
            columns=[
                ColumnDefinition(name="Order ID", data_type=DataType.INTEGER, primary_key=True),
                ColumnDefinition(name="Customer Name", data_type=DataType.STRING),
                ColumnDefinition(name="Total Amount", data_type=DataType.FLOAT),
            ],
        )
        dest.create_schema(schema, if_exists="replace")

        ds = Dataset(
            schema=schema,
            rows=[
                {"Order ID": 101, "Customer Name": "Alice Wonderland", "Total Amount": 250.75},
                {"Order ID": 102, "Customer Name": "Bob Builder", "Total Amount": 120.00},
            ],
        )

        rows_loaded = dest.load(ds, table_name="orders_report", mode="append")
        assert rows_loaded == 2

        # Verify in database directly
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        res = cur.execute('SELECT "Order ID", "Customer Name", "Total Amount" FROM "orders_report" ORDER BY "Order ID"').fetchall()
        conn.close()

        assert len(res) == 2
        assert res[0] == (101, "Alice Wonderland", 250.75)
        assert res[1] == (102, "Bob Builder", 120.00)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_fix_type_inference_mixed_alphanumeric():
    """Verify that type inference does not overwrite STRING with INTEGER, and properly widens types."""
    # Case 1: First value is string, second value is number
    ds1 = Dataset.infer_from_dicts("test1", [
        {"code": "ABC"},
        {"code": "100"},
    ])
    assert ds1.schema_def.get_column("code").data_type == DataType.STRING

    # Case 2: First value is number, second value is string
    ds2 = Dataset.infer_from_dicts("test2", [
        {"code": "100"},
        {"code": "ABC"},
    ])
    assert ds2.schema_def.get_column("code").data_type == DataType.STRING

    # Case 3: Integer widens to Float
    ds3 = Dataset.infer_from_dicts("test3", [
        {"val": "100"},
        {"val": "250.55"},
    ])
    assert ds3.schema_def.get_column("val").data_type == DataType.FLOAT

    # Case 4: Date widens to Datetime
    ds4 = Dataset.infer_from_dicts("test4", [
        {"ts": "2024-01-01"},
        {"ts": "2024-01-01 14:30:00"},
    ])
    assert ds4.schema_def.get_column("ts").data_type == DataType.DATETIME


def test_fix_add_column_transformer_get_output_schema():
    """Verify that AddColumnTransformer respects data_type in get_output_schema."""
    transformer = TransformationRegistry.create(
        TransformerConfig(
            type="add_column",
            params={"name": "priority_level", "value": 1, "data_type": "integer"},
        )
    )
    in_schema = TableSchema(name="tasks", columns=[ColumnDefinition(name="task", data_type=DataType.STRING)])
    out_schema = transformer.get_output_schema(in_schema)

    col = out_schema.get_column("priority_level")
    assert col is not None
    assert col.data_type == DataType.INTEGER


def test_fix_excel_column_discovery():
    """Verify that /api/connector/columns properly parses Excel files."""
    import openpyxl

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        excel_path = f.name

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Patients"
        ws.append(["patient_id", "full_name", "birth_date", "is_active"])
        ws.append([1, "John Doe", "1990-05-15", True])
        wb.save(excel_path)
        wb.close()

        client = TestClient(app)
        res = client.get(f"/api/connector/columns?type=excel&path={excel_path}")
        assert res.status_code == 200
        data = res.json()
        col_names = [c["name"] for c in data["columns"]]
        assert col_names == ["patient_id", "full_name", "birth_date", "is_active"]
    finally:
        if os.path.exists(excel_path):
            os.remove(excel_path)


def test_fix_head_requests_and_health():
    """Verify that root / and /health support HTTP HEAD requests for production health checks."""
    client = TestClient(app)
    res_root = client.head("/")
    assert res_root.status_code == 200

    res_health = client.head("/health")
    assert res_health.status_code == 200

    res_health_get = client.get("/health")
    assert res_health_get.status_code == 200
    assert res_health_get.json()["status"] == "ok"
