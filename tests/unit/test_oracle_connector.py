"""Unit tests for FlowETL Oracle Connector.

Tests OracleSource and OracleDestination implementations:
  - ConnectorRegistry registration
  - Connection URL construction (service_name and SID)
  - Identifier quoting (double-quotes per ANSI/Oracle SQL)
  - TypeRegistry bi-directional mappings (native ↔ canonical)
  - DDL generation with Oracle data types (NUMBER, VARCHAR2, TIMESTAMP)
  - Schema Evolution (ADD, MODIFY, DROP COLUMN)
  - Connector helper URL construction & error formatting
"""

from __future__ import annotations

import pytest
from app.connectors.base import ConnectorConfig
from app.connectors.oracle import OracleDestination, OracleSource
from app.connectors.registry import ConnectorRegistry
from app.schema.evolution import SchemaEvolutionVerifier
from app.schema.models import ColumnDefinition, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from server.api.connector_helper import _build_url, _format_connection_error


def test_oracle_connector_registration() -> None:
    """Verify Oracle source and destination are registered in ConnectorRegistry."""
    src_cls = ConnectorRegistry.get_source_class("oracle")
    dst_cls = ConnectorRegistry.get_destination_class("oracle")
    assert src_cls is OracleSource
    assert dst_cls is OracleDestination


def test_oracle_source_url_building_service_name() -> None:
    """Verify OracleSource builds standard service_name URL."""
    cfg = ConnectorConfig(
        name="test_oracle_src",
        connector_type="oracle",
        options={
            "host": "db.internal",
            "port": 1521,
            "database": "FREEPDB1",
            "user": "system",
            "password": "Password123#",
        },
    )
    src = OracleSource(cfg)
    assert src.dialect == "oracle"
    url = src._build_url()
    assert url == "oracle+oracledb://system:Password123#@db.internal:1521/?service_name=FREEPDB1"


def test_oracle_source_url_building_sid() -> None:
    """Verify OracleSource supports SID connections."""
    cfg = ConnectorConfig(
        name="test_oracle_sid",
        connector_type="oracle",
        options={
            "host": "localhost",
            "port": 1521,
            "sid": "ORCL",
            "user": "scott",
            "password": "tiger",
        },
    )
    src = OracleSource(cfg)
    assert src._build_url() == "oracle+oracledb://scott:tiger@localhost:1521/ORCL"


def test_oracle_destination_url_building() -> None:
    """Verify OracleDestination builds URL with defaults."""
    cfg = ConnectorConfig(
        name="test_oracle_dst",
        connector_type="oracle",
        options={
            "user": "hr",
            "password": "hr",
        },
    )
    dst = OracleDestination(cfg)
    assert dst.dialect == "oracle"
    assert dst._build_url() == "oracle+oracledb://hr:hr@localhost:1521/?service_name=FREEPDB1"


def test_oracle_identifier_quoting() -> None:
    """Verify Oracle identifier quoting with double-quotes."""
    cfg = ConnectorConfig(name="test", connector_type="oracle", options={})
    src = OracleSource(cfg)
    dst = OracleDestination(cfg)

    assert src._quote_identifier("PATIENTS") == '"PATIENTS"'
    assert dst._quote_identifier("table_name") == '"table_name"'
    assert src._quote_identifier('bad"name') == '"bad""name"'


def test_oracle_type_registry_to_canonical() -> None:
    """Verify Oracle native types translate to correct FlowETL canonical DataTypes."""
    assert TypeRegistry.to_canonical("oracle", "NUMBER(1)") == DataType.BOOLEAN
    assert TypeRegistry.to_canonical("oracle", "NUMBER(1,0)") == DataType.BOOLEAN
    assert TypeRegistry.to_canonical("oracle", "BOOLEAN") == DataType.BOOLEAN
    assert TypeRegistry.to_canonical("oracle", "NUMBER(10)") == DataType.INTEGER
    assert TypeRegistry.to_canonical("oracle", "INTEGER") == DataType.INTEGER
    assert TypeRegistry.to_canonical("oracle", "NUMBER(18, 4)") == DataType.DECIMAL
    assert TypeRegistry.to_canonical("oracle", "BINARY_DOUBLE") == DataType.FLOAT
    assert TypeRegistry.to_canonical("oracle", "VARCHAR2(255)") == DataType.STRING
    assert TypeRegistry.to_canonical("oracle", "CLOB") == DataType.STRING
    assert TypeRegistry.to_canonical("oracle", "DATE") == DataType.DATE
    assert TypeRegistry.to_canonical("oracle", "TIMESTAMP(6)") == DataType.DATETIME
    assert TypeRegistry.to_canonical("oracle", "BLOB") == DataType.BINARY
    assert TypeRegistry.to_canonical("oracle", "JSON") == DataType.JSON


def test_oracle_type_registry_to_native() -> None:
    """Verify FlowETL canonical DataTypes translate to proper Oracle DDL types."""
    assert TypeRegistry.to_native("oracle", DataType.INTEGER) == "NUMBER(38)"
    assert TypeRegistry.to_native("oracle", DataType.FLOAT) == "BINARY_DOUBLE"
    assert TypeRegistry.to_native("oracle", DataType.STRING) == "VARCHAR2(255)"
    assert TypeRegistry.to_native("oracle", DataType.STRING, length=500) == "VARCHAR2(500)"
    assert TypeRegistry.to_native("oracle", DataType.DECIMAL, precision=10, scale=2) == "NUMBER(10, 2)"
    assert TypeRegistry.to_native("oracle", DataType.BOOLEAN) == "NUMBER(1)"
    assert TypeRegistry.to_native("oracle", DataType.DATE) == "DATE"
    assert TypeRegistry.to_native("oracle", DataType.DATETIME) == "TIMESTAMP"
    assert TypeRegistry.to_native("oracle", DataType.BINARY) == "BLOB"


def test_oracle_ddl_generation() -> None:
    """Verify DDL generated for Oracle Destination uses Oracle types and quotes."""
    cfg = ConnectorConfig(name="test_dst", connector_type="oracle", options={})
    dst = OracleDestination(cfg)

    schema = TableSchema(
        name="PATIENTS",
        columns=[
            ColumnDefinition(name="ID", data_type=DataType.INTEGER, primary_key=True, nullable=False),
            ColumnDefinition(name="FULL_NAME", data_type=DataType.STRING, nullable=False),
            ColumnDefinition(name="IS_ACTIVE", data_type=DataType.BOOLEAN, nullable=True),
        ],
    )
    ddl = dst._generate_ddl(schema)
    assert 'CREATE TABLE "PATIENTS"' in ddl
    assert '"ID" NUMBER(38) PRIMARY KEY NOT NULL' in ddl
    assert '"FULL_NAME" VARCHAR2(255) NOT NULL' in ddl
    assert '"IS_ACTIVE" NUMBER(1)' in ddl


def test_oracle_schema_evolution() -> None:
    """Verify SchemaEvolutionVerifier generates valid Oracle ALTER TABLE statements."""
    incoming = TableSchema(
        name="STAFF",
        columns=[
            ColumnDefinition(name="ID", data_type=DataType.INTEGER),
            ColumnDefinition(name="BIO", data_type=DataType.STRING, metadata={"length": 1000}),
            ColumnDefinition(name="SALARY", data_type=DataType.DECIMAL),
        ],
    )
    # Existing columns: ID and BIO (currently VARCHAR2(200)), without SALARY
    existing_cols = ["ID", "BIO", "OLD_UNUSED"]
    existing_info = [
        {"name": "ID", "type": "NUMBER(38)"},
        {"name": "BIO", "type": "VARCHAR2(200)"},
        {"name": "OLD_UNUSED", "type": "VARCHAR2(100)"},
    ]

    result = SchemaEvolutionVerifier.verify_and_plan(
        dialect="oracle",
        table_name="STAFF",
        existing_column_names=existing_cols,
        incoming_schema=incoming,
        existing_columns_info=existing_info,
        allow_drop_columns=True,
    )

    assert result.has_drift is True
    # 1. ADD COLUMN SALARY
    add_ddl = [s for s in result.ddl_statements if "ADD" in s]
    assert len(add_ddl) == 1
    assert 'ALTER TABLE "STAFF" ADD COLUMN "SALARY" NUMBER(18, 4) NULL' in add_ddl[0]

    # 2. MODIFY COLUMN BIO (widening from 200 to 1000)
    mod_ddl = [s for s in result.ddl_statements if "MODIFY" in s]
    assert len(mod_ddl) == 1
    assert 'ALTER TABLE "STAFF" MODIFY "BIO" VARCHAR2(1000)' in mod_ddl[0]

    # 3. DROP COLUMN OLD_UNUSED (mirror sync)
    drop_ddl = [s for s in result.ddl_statements if "DROP COLUMN" in s]
    assert len(drop_ddl) == 1
    assert 'ALTER TABLE "STAFF" DROP COLUMN "OLD_UNUSED"' in drop_ddl[0]


def test_connector_helper_oracle_support() -> None:
    """Verify connector helper builds Oracle URL and formats connection errors."""
    url = _build_url("oracle", "10.0.0.1", 1521, "system", "pass", "FREEPDB1")
    assert url == "oracle+oracledb://system:pass@10.0.0.1:1521/?service_name=FREEPDB1"

    # Test error formatter
    err_listener = Exception("ORA-12541: Cannot connect to listener")
    assert "listener Oracle" in _format_connection_error(err_listener)

    err_auth = Exception("ORA-01017: invalid credential")
    assert "Autentikasi Oracle gagal" in _format_connection_error(err_auth)
