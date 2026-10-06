"""Unit tests for Column Selection and Mapping transformers."""

import pytest
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import TransformerConfig
from app.transformations.registry import TransformationRegistry
import app.transformations  # ensure transformers are registered


@pytest.fixture
def sample_dataset() -> Dataset:
    schema = TableSchema(
        name="SourcePatient",
        columns=[
            ColumnDefinition(name="PatientID", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="Name", data_type=DataType.STRING),
            ColumnDefinition(name="Phone", data_type=DataType.STRING),
            ColumnDefinition(name="City", data_type=DataType.STRING),
            ColumnDefinition(name="Age", data_type=DataType.INTEGER),
        ],
    )
    rows = [
        {"PatientID": 1, "Name": "BUDI SANTOSO", "Phone": "081234567890", "City": "Jakarta", "Age": 30},
        {"PatientID": 2, "Name": "SITI AMINAH", "Phone": "081987654321", "City": "Surabaya", "Age": 25},
    ]
    return Dataset(schema=schema, rows=rows)


def test_select_columns_transformer(sample_dataset):
    """Test filtering dataset to only selected columns."""
    cfg = TransformerConfig(type="select_columns", params={"columns": ["Name", "City"]})
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    assert result.column_count == 2
    assert result.schema_def.column_names == ["Name", "City"]
    assert len(result.rows) == 2
    assert result.rows[0] == {"Name": "BUDI SANTOSO", "City": "Jakarta"}
    assert "Phone" not in result.rows[0]
    assert "PatientID" not in result.rows[0]


def test_column_mapping_transformer(sample_dataset):
    """Test mapping source columns to target columns (renaming + projection)."""
    cfg = TransformerConfig(
        type="column_mapping",
        params={
            "mapping": {
                "Name": "nama_pasien",
                "Phone": "no_telepon",
                "City": "domisili",
            },
            "drop_unmapped": True,
            "target_table": "TargetPatient",
        },
    )
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    assert result.schema_def.name == "TargetPatient"
    assert result.column_count == 3
    assert result.schema_def.column_names == ["nama_pasien", "no_telepon", "domisili"]
    # Check data types are preserved
    assert result.schema_def.get_column("nama_pasien").data_type == DataType.STRING
    assert result.schema_def.get_column("no_telepon").data_type == DataType.STRING
    assert result.schema_def.get_column("domisili").data_type == DataType.STRING

    # Check row data
    assert result.rows[0] == {
        "nama_pasien": "BUDI SANTOSO",
        "no_telepon": "081234567890",
        "domisili": "Jakarta",
    }
    assert "Age" not in result.rows[0]
    assert "PatientID" not in result.rows[0]


def test_add_column_transformer(sample_dataset):
    """Test adding a new constant/derived column."""
    cfg = TransformerConfig(
        type="add_column",
        params={"name": "status", "value": "ACTIVE", "data_type": "string"},
    )
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    assert result.column_count == 6
    assert "status" in result.schema_def.column_names
    assert result.rows[0]["status"] == "ACTIVE"
    assert result.rows[1]["status"] == "ACTIVE"
