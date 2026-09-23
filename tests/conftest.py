"""Pytest shared test fixtures for FlowETL test suite."""

import pytest
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


@pytest.fixture
def sample_columns():
    return [
        ColumnDefinition(name="patient_id", data_type=DataType.INTEGER, nullable=False, primary_key=True),
        ColumnDefinition(name="name", data_type=DataType.STRING, nullable=False),
        ColumnDefinition(name="age", data_type=DataType.INTEGER, nullable=True),
        ColumnDefinition(name="diagnosis", data_type=DataType.STRING, nullable=True),
    ]


@pytest.fixture
def sample_table_schema(sample_columns):
    return TableSchema(name="patients", columns=sample_columns)


@pytest.fixture
def sample_dataset(sample_table_schema):
    rows = [
        {"patient_id": 101, "name": "Alice Smith", "age": 42, "diagnosis": "Hypertension"},
        {"patient_id": 102, "name": "Bob Jones", "age": 31, "diagnosis": "Asthma"},
        {"patient_id": 103, "name": "Charlie Brown", "age": 65, "diagnosis": "Diabetes"},
    ]
    return Dataset(schema=sample_table_schema, rows=rows)
