"""Integration test: End-to-end multi-connector pipelines across CSV, SQLite, and JSON."""

import csv
import json
from pathlib import Path
import pytest

from app.connectors.base import ConnectorConfig
from app.connectors.csv import CSVSource
from app.connectors.json import JSONDestination, JSONSource
from app.connectors.sqlite import SQLiteDestination, SQLiteSource
from app.core.context import PipelineRunStatus
from app.core.pipeline import Pipeline
from app.schema.mapper import ColumnMappingConfig, SchemaMapper
from app.schema.models import Dataset, DataType, TableSchema
from app.transformations.base import Transformer, TransformerConfig


class SchemaMapperStep(Transformer):
    def __init__(self, config: TransformerConfig, mapper: SchemaMapper) -> None:
        super().__init__(config)
        self.mapper = mapper

    def transform(self, dataset: Dataset) -> Dataset:
        return self.mapper.map_dataset(dataset)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return self.mapper.map_schema(input_schema)


class AdultPatientFilter(Transformer):
    def transform(self, dataset: Dataset) -> Dataset:
        return Dataset(
            schema=dataset.schema_def,
            rows=[r for r in dataset.rows if r.get("patient_age", 0) >= 18],
        )

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


def test_end_to_end_csv_to_sqlite_to_json(tmp_path: Path):
    # 1. Create a raw CSV source file
    csv_path = tmp_path / "raw_patients.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "raw_name", "raw_age", "diagnosis", "admission_status"])
        writer.writerow(["1001", "alice smith", "29", "Hypertension", "admitted"])
        writer.writerow(["1002", "bob marley", "45", "Asthma", "discharged"])
        writer.writerow(["1003", "timmy turner", "10", "Flu", "discharged"])  # Minor: should be filtered
        writer.writerow(["1004", "diana prince", "34", "", "admitted"])       # Empty diagnosis: will get default

    # 2. Pipeline 1: CSV -> SchemaMapper & Filter -> SQLite Database
    sqlite_db_path = tmp_path / "hospital_warehouse.db"

    csv_source = CSVSource(
        ConnectorConfig(name="csv_raw", connector_type="csv", options={"path": str(csv_path)})
    )
    sqlite_dest = SQLiteDestination(
        ConnectorConfig(name="sqlite_dw", connector_type="sqlite", options={"database": str(sqlite_db_path)})
    )

    mapper = SchemaMapper(
        target_table_name="dim_patients",
        column_mappings=[
            ColumnMappingConfig(source_column="id", target_column="patient_id", target_type=DataType.INTEGER, primary_key=True),
            ColumnMappingConfig(source_column="raw_name", target_column="patient_name", target_type=DataType.STRING),
            ColumnMappingConfig(source_column="raw_age", target_column="patient_age", target_type=DataType.INTEGER),
            ColumnMappingConfig(source_column="diagnosis", target_column="condition", target_type=DataType.STRING, default_value="General Checkup"),
        ],
        drop_unmapped=True,
    )

    t_map = SchemaMapperStep(TransformerConfig(type="schema_mapper"), mapper=mapper)
    t_filter = AdultPatientFilter(TransformerConfig(type="filter"))

    pipeline1 = Pipeline(
        name="csv_to_sqlite_pipeline",
        source=csv_source,
        destination=sqlite_dest,
        source_table="raw_patients",
        destination_table="dim_patients",
        transformations=[t_map, t_filter],
        load_mode="replace",
    )

    ctx1 = pipeline1.run()
    assert ctx1.status == PipelineRunStatus.SUCCESS
    assert ctx1.metrics.rows_extracted == 4
    assert ctx1.metrics.rows_transformed == 3  # Minor filtered out
    assert ctx1.metrics.rows_loaded == 3

    # 3. Pipeline 2: SQLite Table -> FlowETL -> JSON Export
    json_export_path = tmp_path / "dim_patients_export.json"

    sqlite_source = SQLiteSource(
        ConnectorConfig(name="sqlite_dw", connector_type="sqlite", options={"database": str(sqlite_db_path)})
    )
    json_dest = JSONDestination(
        ConnectorConfig(name="json_export", connector_type="json", options={"path": str(json_export_path)})
    )

    pipeline2 = Pipeline(
        name="sqlite_to_json_pipeline",
        source=sqlite_source,
        destination=json_dest,
        source_table="dim_patients",
        destination_table="dim_patients_export",
        transformations=[],
        load_mode="replace",
    )

    ctx2 = pipeline2.run()
    assert ctx2.status == PipelineRunStatus.SUCCESS
    assert ctx2.metrics.rows_extracted == 3
    assert ctx2.metrics.rows_loaded == 3

    # 4. Verify Final JSON File Content
    assert json_export_path.exists()
    with open(json_export_path, "r") as f:
        exported_records = json.load(f)

    assert len(exported_records) == 3
    assert exported_records[0]["patient_id"] == 1001
    assert exported_records[0]["patient_name"] == "alice smith"
    assert exported_records[0]["patient_age"] == 29
    assert exported_records[0]["condition"] == "Hypertension"
    # Check default value substitution
    assert exported_records[2]["patient_id"] == 1004
    assert exported_records[2]["condition"] == "General Checkup"
