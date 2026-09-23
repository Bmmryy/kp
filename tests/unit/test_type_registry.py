"""Unit tests for TypeRegistry bi-directional dialect mapping."""

import pytest
from app.core.exceptions import SchemaMappingError
from app.schema.models import DataType
from app.schema.type_registry import TypeRegistry


class TestTypeRegistry:
    def test_mysql_to_canonical(self):
        assert TypeRegistry.to_canonical("mysql", "INT") == DataType.INTEGER
        assert TypeRegistry.to_canonical("mysql", "BIGINT(20)") == DataType.INTEGER
        assert TypeRegistry.to_canonical("mysql", "TINYINT(1)") == DataType.BOOLEAN
        assert TypeRegistry.to_canonical("mysql", "VARCHAR(128)") == DataType.STRING
        assert TypeRegistry.to_canonical("mysql", "DATETIME") == DataType.DATETIME
        assert TypeRegistry.to_canonical("mysql", "DECIMAL(10, 2)") == DataType.DECIMAL
        assert TypeRegistry.to_canonical("mysql", "JSON") == DataType.JSON

    def test_postgres_to_canonical(self):
        assert TypeRegistry.to_canonical("postgresql", "INTEGER") == DataType.INTEGER
        assert TypeRegistry.to_canonical("postgresql", "BIGSERIAL") == DataType.INTEGER
        assert TypeRegistry.to_canonical("postgresql", "DOUBLE PRECISION") == DataType.FLOAT
        assert TypeRegistry.to_canonical("postgresql", "CHARACTER VARYING(50)") == DataType.STRING
        assert TypeRegistry.to_canonical("postgresql", "TIMESTAMPTZ") == DataType.DATETIME
        assert TypeRegistry.to_canonical("postgresql", "BOOLEAN") == DataType.BOOLEAN
        assert TypeRegistry.to_canonical("postgresql", "JSONB") == DataType.JSON

    def test_sqlite_to_canonical(self):
        assert TypeRegistry.to_canonical("sqlite", "INTEGER") == DataType.INTEGER
        assert TypeRegistry.to_canonical("sqlite", "TEXT") == DataType.STRING
        assert TypeRegistry.to_canonical("sqlite", "REAL") == DataType.FLOAT

    def test_canonical_to_native_target(self):
        # Postgres targets
        assert TypeRegistry.to_native("postgresql", DataType.INTEGER) == "INTEGER"
        assert TypeRegistry.to_native("postgresql", DataType.DATETIME) == "TIMESTAMP"
        assert TypeRegistry.to_native("postgresql", DataType.JSON) == "JSONB"
        assert TypeRegistry.to_native("postgresql", DataType.STRING, length=100) == "VARCHAR(100)"

        # MySQL targets
        assert TypeRegistry.to_native("mysql", DataType.INTEGER) == "INT"
        assert TypeRegistry.to_native("mysql", DataType.BOOLEAN) == "TINYINT(1)"
        assert TypeRegistry.to_native("mysql", DataType.JSON) == "JSON"

    def test_custom_dialect_registration(self):
        TypeRegistry.register_native_mapping("custom_db", r"^number_id$", DataType.INTEGER)
        TypeRegistry.register_native_target("custom_db", DataType.INTEGER, "NUM_ID")

        assert TypeRegistry.to_canonical("custom_db", "number_id") == DataType.INTEGER
        assert TypeRegistry.to_native("custom_db", DataType.INTEGER) == "NUM_ID"

    def test_unknown_type_handling(self):
        with pytest.raises(SchemaMappingError) as exc_info:
            TypeRegistry.to_canonical("postgresql", "UNKNOWN_NON_EXISTENT_TYPE_XYZ")
        assert "Unsupported native type" in exc_info.value.message
