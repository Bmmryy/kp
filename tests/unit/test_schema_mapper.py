"""Unit tests for SchemaMapper engine and column mapping translations."""

import pytest
from app.core.exceptions import SchemaMappingError
from app.schema.mapper import ColumnMappingConfig, SchemaMapper
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class TestSchemaMapper:
    def test_identity_mapping(self, sample_table_schema, sample_dataset):
        mapper = SchemaMapper(target_table_name="target_patients")
        target_schema = mapper.map_schema(sample_table_schema)

        assert target_schema.name == "target_patients"
        assert target_schema.column_names == sample_table_schema.column_names

        mapped_dataset = mapper.map_dataset(sample_dataset)
        assert mapped_dataset.row_count == 3
        assert mapped_dataset.rows[0]["name"] == "Alice Smith"

    def test_column_rename_and_retype(self, sample_table_schema):
        raw_dataset = Dataset(
            schema=sample_table_schema,
            rows=[
                {"patient_id": "1001", "name": "Alice Smith", "age": "42", "diagnosis": "Hypertension"},
                {"patient_id": "1002", "name": "Bob Jones", "age": "31", "diagnosis": None},
            ],
        )

        mappings = [
            ColumnMappingConfig(
                source_column="patient_id",
                target_column="id",
                target_type=DataType.INTEGER,
                primary_key=True,
            ),
            ColumnMappingConfig(
                source_column="name",
                target_column="full_name",
                target_type=DataType.STRING,
            ),
            ColumnMappingConfig(
                source_column="age",
                target_column="patient_age",
                target_type=DataType.INTEGER,
            ),
            ColumnMappingConfig(
                source_column="diagnosis",
                target_column="condition",
                target_type=DataType.STRING,
                default_value="General Checkup",
            ),
        ]

        mapper = SchemaMapper(
            target_table_name="dim_patients",
            column_mappings=mappings,
            drop_unmapped=True,
        )

        target_schema = mapper.map_schema(sample_table_schema)
        assert target_schema.name == "dim_patients"
        assert target_schema.column_names == ["id", "full_name", "patient_age", "condition"]
        assert target_schema.get_column("id").primary_key is True

        mapped_data = mapper.map_dataset(raw_dataset)
        assert mapped_data.row_count == 2
        first_row = mapped_data.rows[0]
        second_row = mapped_data.rows[1]

        # Verify type casting and rename
        assert first_row["id"] == 1001
        assert isinstance(first_row["id"], int)
        assert first_row["full_name"] == "Alice Smith"
        assert first_row["patient_age"] == 42
        assert first_row["condition"] == "Hypertension"

        # Verify default value substitution on null
        assert second_row["condition"] == "General Checkup"

    def test_missing_source_column_error(self, sample_table_schema):
        mappings = [
            ColumnMappingConfig(
                source_column="non_existent_column",
                target_column="target_col",
            )
        ]
        mapper = SchemaMapper(target_table_name="target", column_mappings=mappings)
        with pytest.raises(SchemaMappingError) as exc_info:
            mapper.map_schema(sample_table_schema)
        assert "Mapped source column 'non_existent_column' does not exist" in exc_info.value.message
