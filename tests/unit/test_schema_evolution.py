"""Unit tests for Verified Schema Evolution (Schema Drift Detection)."""

from app.schema.evolution import SchemaEvolutionVerifier
from app.schema.models import ColumnDefinition, DataType, TableSchema


def test_schema_evolution_no_drift():
    existing_cols = ["id", "name", "email"]
    schema = TableSchema(
        name="users",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="email", data_type=DataType.STRING),
        ],
    )
    res = SchemaEvolutionVerifier.verify_and_plan("mysql", "users", existing_cols, schema)
    assert res.has_drift is False
    assert len(res.new_columns) == 0
    assert len(res.ddl_statements) == 0


def test_schema_evolution_detects_new_column_mysql():
    existing_cols = ["id", "name"]
    schema = TableSchema(
        name="users",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="phone", data_type=DataType.STRING),
            ColumnDefinition(name="age", data_type=DataType.INTEGER),
        ],
    )
    res = SchemaEvolutionVerifier.verify_and_plan("mysql", "users", existing_cols, schema)
    assert res.has_drift is True
    assert len(res.new_columns) == 2
    assert [c.name for c in res.new_columns] == ["phone", "age"]
    assert len(res.ddl_statements) == 2
    assert 'ALTER TABLE "users" ADD COLUMN "phone"' in res.ddl_statements[0]
    assert "NULL" in res.ddl_statements[0]
    assert 'ALTER TABLE "users" ADD COLUMN "age"' in res.ddl_statements[1]


def test_schema_evolution_sqlite_ddl():
    existing_cols = ["id"]
    schema = TableSchema(
        name="products",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="price", data_type=DataType.FLOAT),
        ],
    )
    res = SchemaEvolutionVerifier.verify_and_plan("sqlite", "products", existing_cols, schema)
    assert res.has_drift is True
    assert len(res.ddl_statements) == 1
    assert 'ALTER TABLE "products" ADD COLUMN "price"' in res.ddl_statements[0]
