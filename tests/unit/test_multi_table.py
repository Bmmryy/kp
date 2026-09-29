"""Unit tests for Multi-Table Merging and In-Memory JoinTransformer."""

from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import TransformerConfig
from app.transformations.registry import TransformationRegistry
import app.transformations  # ensure join transformer is registered


def test_in_memory_inner_join():
    # Table A: Patients
    schema_a = TableSchema(
        name="patients",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="dept_id", data_type=DataType.INTEGER),
        ],
    )
    rows_a = [
        {"id": 1, "name": "Budi", "dept_id": 10},
        {"id": 2, "name": "Siti", "dept_id": 20},
        {"id": 3, "name": "Agus", "dept_id": 99},  # No match in Table B
    ]
    ds_a = Dataset(schema=schema_a, rows=rows_a)

    # Table B: Departments
    rows_b = [
        {"dept_id": 10, "department_name": "Kardiologi"},
        {"dept_id": 20, "department_name": "Neurologi"},
    ]

    cfg = TransformerConfig(
        type="join",
        params={
            "right_rows": rows_b,
            "left_on": "dept_id",
            "right_on": "dept_id",
            "join_type": "inner",
        },
    )
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(ds_a)

    assert len(result.rows) == 2
    assert result.rows[0]["name"] == "Budi"
    assert result.rows[0]["department_name"] == "Kardiologi"
    assert result.rows[1]["name"] == "Siti"
    assert result.rows[1]["department_name"] == "Neurologi"


def test_in_memory_left_join():
    schema_a = TableSchema(
        name="patients",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER),
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="dept_id", data_type=DataType.INTEGER),
        ],
    )
    rows_a = [
        {"id": 1, "name": "Budi", "dept_id": 10},
        {"id": 2, "name": "Agus", "dept_id": 99},
    ]
    ds_a = Dataset(schema=schema_a, rows=rows_a)

    rows_b = [{"dept_id": 10, "dept_name": "Poli Umum"}]

    cfg = TransformerConfig(
        type="join",
        params={
            "right_rows": rows_b,
            "left_on": "dept_id",
            "right_on": "dept_id",
            "join_type": "left",
        },
    )
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(ds_a)

    assert len(result.rows) == 2
    assert result.rows[0]["dept_name"] == "Poli Umum"
    assert result.rows[1]["dept_name"] is None
