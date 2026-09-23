"""Unit tests for internal data model and canonical schemas."""

import pytest
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class TestDataType:
    def test_from_str_standard(self):
        assert DataType.from_str("int") == DataType.INTEGER
        assert DataType.from_str("VARCHAR") == DataType.STRING
        assert DataType.from_str("boolean") == DataType.BOOLEAN
        assert DataType.from_str("TIMESTAMP") == DataType.DATETIME
        assert DataType.from_str("numeric") == DataType.DECIMAL

    def test_from_str_unknown(self):
        with pytest.raises(ValueError, match="Unknown data type"):
            DataType.from_str("unknown_type_xyz")


class TestTableSchema:
    def test_schema_properties(self, sample_table_schema):
        assert sample_table_schema.name == "patients"
        assert sample_table_schema.column_names == ["patient_id", "name", "age", "diagnosis"]
        assert sample_table_schema.primary_keys == ["patient_id"]

    def test_get_column(self, sample_table_schema):
        col = sample_table_schema.get_column("name")
        assert col is not None
        assert col.data_type == DataType.STRING
        assert col.nullable is False

        assert sample_table_schema.get_column("non_existent") is None

    def test_add_and_drop_column(self, sample_table_schema):
        new_col = ColumnDefinition(name="room_number", data_type=DataType.INTEGER)
        sample_table_schema.add_column(new_col)
        assert sample_table_schema.has_column("room_number")

        with pytest.raises(ValueError, match="already exists"):
            sample_table_schema.add_column(new_col)

        sample_table_schema.drop_column("room_number")
        assert not sample_table_schema.has_column("room_number")

    def test_rename_column(self, sample_table_schema):
        sample_table_schema.rename_column("name", "patient_full_name")
        assert sample_table_schema.has_column("patient_full_name")
        assert not sample_table_schema.has_column("name")


class TestDataset:
    def test_dataset_basics(self, sample_dataset):
        assert sample_dataset.row_count == 3
        assert sample_dataset.column_count == 4
        sample_head = sample_dataset.head(2)
        assert sample_head.row_count == 2
        assert sample_head.rows[0]["name"] == "Alice Smith"

    def test_infer_from_dicts(self):
        records = [
            {"id": 1, "active": True, "score": 98.5, "city": "Seattle"},
            {"id": 2, "active": False, "score": 85.0, "city": "Portland"},
        ]
        dataset = Dataset.infer_from_dicts(name="scores", rows=records)
        assert dataset.row_count == 2
        assert dataset.schema_def.has_column("id")
        assert dataset.schema_def.has_column("active")
        assert dataset.schema_def.get_column("id").primary_key is True
        assert dataset.schema_def.get_column("active").data_type == DataType.BOOLEAN
