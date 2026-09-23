"""FlowETL — Production Demonstration (Steps 1 to 4).

Demonstrates:
1. Universal TypeRegistry (Cross-dialect SQL type translations).
2. Real CSV file extraction via CSVSource.
3. SchemaMapper transformation & adult patient filtering.
4. Real SQLite relational database loading (DDL generation + batch insert).
5. Downstream extraction from SQLite and export into clean JSON.
"""

from pathlib import Path

from app.connectors.base import ConnectorConfig
from app.connectors.csv import CSVSource
from app.connectors.json import JSONDestination
from app.connectors.sqlite import SQLiteDestination, SQLiteSource
from app.core.context import PipelineRunStatus
from app.core.pipeline import Pipeline
from app.schema.mapper import ColumnMappingConfig, SchemaMapper
from app.schema.models import Dataset, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from app.transformations.base import Transformer, TransformerConfig


class SchemaMapperStep(Transformer):
    """Transformer applying SchemaMapper rules to datasets."""

    def __init__(self, config: TransformerConfig, mapper: SchemaMapper) -> None:
        super().__init__(config)
        self.mapper = mapper

    def transform(self, dataset: Dataset) -> Dataset:
        return self.mapper.map_dataset(dataset)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return self.mapper.map_schema(input_schema)


class AdultPatientFilter(Transformer):
    """Filters records to include only adult patients (patient_age >= 18)."""

    def transform(self, dataset: Dataset) -> Dataset:
        min_age = self.config.params.get("min_age", 18)
        filtered = [r for r in dataset.rows if r.get("patient_age", 0) >= min_age]
        return Dataset(schema=dataset.schema_def, rows=filtered)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


def main() -> None:
    print("=" * 72)
    print(" FlowETL — Visual Data Integration Platform (Steps 1–4 Demo)")
    print("=" * 72)

    # 1. TypeRegistry Dialect Mapping
    print("\n[1. TypeRegistry: Canonical Cross-Dialect Translations]")
    sample_types = [
        ("INT", "mysql", "postgresql"),
        ("VARCHAR(100)", "mysql", "postgresql"),
        ("TINYINT(1)", "mysql", "postgresql"),
        ("DATETIME", "mysql", "postgresql"),
        ("DECIMAL(10, 2)", "mysql", "postgresql"),
        ("JSON", "mysql", "postgresql"),
    ]
    print(f" {'Source Type (MySQL)':<22} ──▶ {'Canonical Type':<16} ──▶ {'Target DDL (PostgreSQL)':<24}")
    print(" " + "─" * 66)
    for src_type, src_dialect, target_dialect in sample_types:
        canonical = TypeRegistry.to_canonical(src_dialect, src_type)
        target_ddl = TypeRegistry.to_native(target_dialect, canonical)
        print(f" {src_type:<22} ──▶ {canonical.value:<16} ──▶ {target_ddl:<24}")

    # Paths
    base_dir = Path(__file__).parent / "examples"
    csv_file = base_dir / "hospital_patients.csv"
    sqlite_file = base_dir / "hospital_dw.sqlite"
    json_file = base_dir / "hospital_patients_clean.json"

    # 2. Pipeline 1: CSV -> SQLite
    print(f"\n[2. Pipeline 1: CSV ──▶ SchemaMapper + Filter ──▶ SQLite]")
    print(f" Source CSV : {csv_file.name}")
    print(f" Target DB  : {sqlite_file.name}")

    csv_source = CSVSource(
        ConnectorConfig(
            name="Hospital_CSV_Source",
            connector_type="csv",
            options={"path": str(csv_file)},
        )
    )
    sqlite_dest = SQLiteDestination(
        ConnectorConfig(
            name="Hospital_SQLite_Target",
            connector_type="sqlite",
            options={"database": str(sqlite_file)},
        )
    )

    mapper = SchemaMapper(
        target_table_name="dim_patients",
        column_mappings=[
            ColumnMappingConfig(source_column="Patient_ID", target_column="patient_id", target_type=DataType.INTEGER, primary_key=True),
            ColumnMappingConfig(source_column="Patient_Name", target_column="full_name", target_type=DataType.STRING),
            ColumnMappingConfig(source_column="Age", target_column="patient_age", target_type=DataType.INTEGER),
            ColumnMappingConfig(source_column="Gender", target_column="gender", target_type=DataType.STRING),
            ColumnMappingConfig(source_column="Medical_Condition", target_column="diagnosis", target_type=DataType.STRING),
            ColumnMappingConfig(source_column="Billing_Amount", target_column="billing_amount", target_type=DataType.DECIMAL),
            ColumnMappingConfig(source_column="Doctor", target_column="attending_physician", target_type=DataType.STRING),
        ],
        drop_unmapped=True,
    )

    t_map = SchemaMapperStep(TransformerConfig(type="schema_mapper"), mapper=mapper)
    t_filter = AdultPatientFilter(TransformerConfig(type="filter", params={"min_age": 18}))

    p1 = Pipeline(
        name="csv_to_sqlite_migration",
        source=csv_source,
        destination=sqlite_dest,
        source_table="hospital_patients",
        destination_table="dim_patients",
        transformations=[t_map, t_filter],
        load_mode="replace",
    )

    ctx1 = p1.run()

    print("\n" + "─" * 72)
    print(f" ✓ Pipeline 1 Completed ({ctx1.status.value})")
    print(f" Extracted: {ctx1.metrics.rows_extracted} | Transformed: {ctx1.metrics.rows_transformed} | Loaded: {ctx1.metrics.rows_loaded} | Duration: {ctx1.metrics.duration_seconds}s")
    print("─" * 72)

    # 3. Pipeline 2: SQLite -> JSON Export
    print(f"\n[3. Pipeline 2: SQLite ──▶ FlowETL ──▶ JSON Export]")
    sqlite_source = SQLiteSource(
        ConnectorConfig(
            name="Hospital_SQLite_Source",
            connector_type="sqlite",
            options={"database": str(sqlite_file)},
        )
    )
    json_dest = JSONDestination(
        ConnectorConfig(
            name="Clean_JSON_Export",
            connector_type="json",
            options={"path": str(json_file)},
        )
    )

    p2 = Pipeline(
        name="sqlite_to_json_export",
        source=sqlite_source,
        destination=json_dest,
        source_table="dim_patients",
        destination_table="dim_patients_export",
        load_mode="replace",
    )

    ctx2 = p2.run()

    print("\n" + "─" * 72)
    print(f" ✓ Pipeline 2 Completed ({ctx2.status.value})")
    print(f" Extracted: {ctx2.metrics.rows_extracted} | Loaded: {ctx2.metrics.rows_loaded} | Duration: {ctx2.metrics.duration_seconds}s")
    print("─" * 72)

    # 4. Preview Target JSON records
    print(f"\n[4. Destination JSON Preview ({json_file.name})]")
    import json
    with open(json_file, "r") as f:
        records = json.load(f)

    for r in records[:5]:
        print(f"  • ID: {r['patient_id']} | Name: {r['full_name']:<18} | Age: {r['patient_age']} | Dx: {r['diagnosis']:<14} | Bill: ${float(r['billing_amount']):,.2f}")

    print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
