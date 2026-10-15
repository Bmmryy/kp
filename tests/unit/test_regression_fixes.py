"""Comprehensive Unit & Regression Tests for BUG-001 through BUG-004 Fixes."""

import pytest
import sqlite3
import tempfile
import os
from app.connectors.sqlite import SQLiteSource, SQLiteDestination
from app.connectors.mysql import MySQLSource, MySQLDestination
from app.connectors.postgresql import PostgreSQLSource, PostgreSQLDestination
from app.connectors.base import ConnectorConfig
from app.core.pipeline import Pipeline
from app.schema.models import TableSchema, ColumnDefinition, DataType, Dataset
from app.schema.evolution import SchemaEvolutionVerifier
from app.services.scheduler import scheduler, ScheduledJob, INTERVAL_MAP
from app.transformations.registry import TransformationRegistry
from app.transformations.base import TransformerConfig


def test_bug001_sql_identifier_quoting_spaces_and_keywords():
    """Verify BUG-001 fix: Tables and columns with spaces & reserved keywords are quoted safely."""
    temp_dir = tempfile.mkdtemp()
    db_src = os.path.join(temp_dir, "test_quotes_src.db")
    db_dst = os.path.join(temp_dir, "test_quotes_dst.db")

    conn = sqlite3.connect(db_src)
    conn.cursor().execute('CREATE TABLE "ORDER TABLE" ("SELECT" INTEGER PRIMARY KEY, "GROUP BY" TEXT)')
    conn.cursor().execute('INSERT INTO "ORDER TABLE" VALUES (101, \'Critical Patient\')')
    conn.commit()
    conn.close()

    source = SQLiteSource(ConnectorConfig(name="s", connector_type="sqlite", options={"database": db_src}))
    dest = SQLiteDestination(ConnectorConfig(name="d", connector_type="sqlite", options={"database": db_dst}))

    p = Pipeline(
        name="test_quoted_identifiers",
        source=source,
        destination=dest,
        source_table="ORDER TABLE",
        destination_table="ORDER TABLE",
        load_mode="replace"
    )
    ctx = p.run()
    assert ctx.status.value == "SUCCESS", f"Pipeline failed: {ctx.errors}"
    assert ctx.metrics.rows_extracted == 1
    assert ctx.metrics.rows_loaded == 1

    conn_dst = sqlite3.connect(db_dst)
    rows = conn_dst.cursor().execute('SELECT "SELECT", "GROUP BY" FROM "ORDER TABLE"').fetchall()
    conn_dst.close()
    assert len(rows) == 1
    assert rows[0] == (101, 'Critical Patient')


def test_bug001_mysql_and_postgres_quote_escaping():
    """Verify MySQL backtick escaping and Postgres double quote escaping."""
    my_src = MySQLSource(ConnectorConfig(name="m", connector_type="mysql", options={}))
    assert my_src._quote_identifier("order") == "`order`"
    assert my_src._quote_identifier("tbl`test") == "`tbl``test`"

    pg_src = PostgreSQLSource(ConnectorConfig(name="p", connector_type="postgresql", options={}))
    assert pg_src._quote_identifier("order") == '"order"'
    assert pg_src._quote_identifier('tbl"test') == '"tbl""test"'


def test_bug002_sync_mode_when_source_is_empty():
    """Verify BUG-002 fix: Sync/mirror mode clears destination table when source is empty."""
    temp_dir = tempfile.mkdtemp()
    db_src = os.path.join(temp_dir, "empty_src.db")
    db_dst = os.path.join(temp_dir, "full_dst.db")

    # Source has 0 rows
    conn = sqlite3.connect(db_src)
    conn.cursor().execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()

    # Destination initially has 3 rows
    conn = sqlite3.connect(db_dst)
    conn.cursor().execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, name TEXT)")
    conn.cursor().execute("INSERT INTO patients VALUES (1, 'Old Alice'), (2, 'Old Bob'), (3, 'Old Charlie')")
    conn.commit()
    conn.close()

    source = SQLiteSource(ConnectorConfig(name="s", connector_type="sqlite", options={"database": db_src}))
    dest = SQLiteDestination(ConnectorConfig(name="d", connector_type="sqlite", options={"database": db_dst}))

    p = Pipeline(
        name="test_sync_empty_source",
        source=source,
        destination=dest,
        source_table="patients",
        destination_table="patients",
        load_mode="sync"
    )
    ctx = p.run()
    assert ctx.status.value == "SUCCESS"
    assert ctx.metrics.rows_extracted == 0
    assert ctx.metrics.rows_loaded == 0

    # Destination MUST be empty now (0 rows)
    conn_dst = sqlite3.connect(db_dst)
    cnt = conn_dst.cursor().execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    conn_dst.close()
    assert cnt == 0, f"Expected 0 rows in destination, found {cnt}"


def test_bug003_schema_evolution_length_widening_detection():
    """Verify BUG-003 fix: Schema evolution detects VARCHAR(50) -> VARCHAR(255) capacity widening."""
    incoming_schema = TableSchema(
        name="dim_patients",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER),
            ColumnDefinition(
                name="name",
                data_type=DataType.STRING,
                metadata={"raw_type": "VARCHAR(255)", "length": 255}
            )
        ]
    )
    existing_cols_info = [
        {"name": "id", "type": "INT"},
        {"name": "name", "type": "VARCHAR(50)"}
    ]

    evo = SchemaEvolutionVerifier.verify_and_plan(
        dialect="mysql",
        table_name="dim_patients",
        existing_column_names=["id", "name"],
        incoming_schema=incoming_schema,
        quote_fn=lambda x: f"`{x}`",
        existing_columns_info=existing_cols_info
    )

    assert evo.has_drift is True
    assert len(evo.ddl_statements) == 1
    assert "MODIFY COLUMN `name` VARCHAR(255)" in evo.ddl_statements[0]


def test_bug004_scheduler_invalid_frequency_rejected():
    """Verify BUG-004 fix: Invalid/unsupported scheduler intervals raise ValueError and are not quietly defaulted to 1 hour."""
    job = ScheduledJob(
        id="j1",
        name="Test Job",
        pipeline_name="P",
        source_type="sqlite",
        source_options={},
        destination_type="sqlite",
        destination_options={},
        frequency="invalid_cron_or_2m"
    )

    with pytest.raises(ValueError, match="tidak valid atau belum didukung"):
        job.calculate_next_run()


def test_generic_filter_transformer_registered():
    """Verify Generic FilterTransformer is registered and filters correctly."""
    assert "filter" in TransformationRegistry.list_available()

    ds = Dataset(
        schema=TableSchema(name="t", columns=[
            ColumnDefinition(name="name", data_type=DataType.STRING),
            ColumnDefinition(name="age", data_type=DataType.INTEGER),
            ColumnDefinition(name="city", data_type=DataType.STRING),
        ]),
        rows=[
            {"name": "Alice", "age": 25, "city": "Jakarta"},
            {"name": "Bob", "age": 17, "city": "Surabaya"},
            {"name": "Charlie", "age": 30, "city": "Bandung"},
        ]
    )

    t = TransformationRegistry.create(TransformerConfig(type="filter", params={"column": "age", "operator": ">=", "value": 18}))
    res = t.transform(ds)
    assert len(res.rows) == 2
    assert [r["name"] for r in res.rows] == ["Alice", "Charlie"]

    # String contains
    t_str = TransformationRegistry.create(TransformerConfig(type="filter", params={"column": "city", "operator": "contains", "value": "karta"}))
    res_str = t_str.transform(ds)
    assert len(res_str.rows) == 1
    assert res_str.rows[0]["name"] == "Alice"


def test_column_mapping_duplicate_detection_and_ignore_handling():
    """Verify that multiple __ignore__ columns do not collide, but actual duplicate target columns raise error."""
    from app.core.exceptions import TransformationError
    import app.transformations.column_mapping

    ds = Dataset(
        schema=TableSchema(name="bed", columns=[
            ColumnDefinition(name="bed_No", data_type=DataType.STRING),
            ColumnDefinition(name="bed_Type", data_type=DataType.STRING),
            ColumnDefinition(name="ward_No", data_type=DataType.STRING),
        ]),
        rows=[{"bed_No": "B01", "bed_Type": "VIP", "ward_No": "W10"}]
    )

    # 1. Multiple __ignore__ should NOT collide
    valid_trans = TransformationRegistry.create(TransformerConfig(
        type="column_mapping",
        params={
            "mapping": {
                "bed_No": "dept_Id",
                "bed_Type": "__ignore__",
                "ward_No": "__ignore__",
            },
            "drop_unmapped": True,
            "target_table": "Department",
        }
    ))
    res = valid_trans.transform(ds)
    assert len(res.rows) == 1
    assert "dept_Id" in res.rows[0]
    assert "bed_Type" not in res.rows[0]
    assert "ward_No" not in res.rows[0]

    # 2. Actual duplicate target columns should raise TransformationError with clear details
    dup_trans = TransformationRegistry.create(TransformerConfig(
        type="column_mapping",
        params={
            "mapping": {
                "bed_No": "dept_Id",
                "ward_No": "dept_Id",
            },
            "drop_unmapped": True,
            "target_table": "Department",
        }
    ))
    with pytest.raises(TransformationError, match="Dua kolom sumber.*dipetakan ke kolom target yang sama 'dept_Id'"):
        dup_trans.transform(ds)


# ── New tests for type inference and structural sync ──────────────────────────

def test_cast_columns_transformer_basic():
    """CastColumnsTransformer harus mengubah tipe data kolom sesuai mapping."""
    import app.transformations  # noqa: F401
    trans = TransformationRegistry.create(
        TransformerConfig(type="cast_columns", params={
            "column_types": {
                "age": "integer",
                "salary": "float",
                "is_active": "boolean",
            }
        })
    )
    ds = Dataset.infer_from_dicts(name="test", rows=[
        {"name": "Andi", "age": "28", "salary": "5000.50", "is_active": "true"},
        {"name": "Budi", "age": "35", "salary": "7200",    "is_active": "false"},
    ])
    result = trans.transform(ds)
    assert result.rows[0]["age"] == 28
    assert isinstance(result.rows[0]["salary"], float)
    assert result.rows[0]["is_active"] is True
    assert result.rows[1]["is_active"] is False
    # Kolom name tidak diubah
    assert result.rows[0]["name"] == "Andi"


def test_cast_columns_transformer_schema_update():
    """Output schema dari CastColumnsTransformer harus mencerminkan tipe baru."""
    import app.transformations  # noqa: F401
    trans = TransformationRegistry.create(
        TransformerConfig(type="cast_columns", params={
            "column_types": {"qty": "integer"}
        })
    )
    ds = Dataset.infer_from_dicts(name="test", rows=[{"qty": "10", "label": "A"}])
    result = trans.transform(ds)
    qty_col = next(c for c in result.schema_def.columns if c.name == "qty")
    assert qty_col.data_type == DataType.INTEGER


def test_schema_evolution_drop_columns_mirror_mode():
    """verify_and_plan dengan allow_drop_columns=True harus generate DROP COLUMN DDL
    untuk kolom yang ada di destination tapi tidak ada di source."""
    incoming = TableSchema(name="tbl", columns=[
        ColumnDefinition(name="id",   data_type=DataType.INTEGER),
        ColumnDefinition(name="name", data_type=DataType.STRING),
    ])
    # Destination punya 3 kolom: id, name, old_col (orphan)
    existing = ["id", "name", "old_col"]
    result = SchemaEvolutionVerifier.verify_and_plan(
        dialect="mysql",
        table_name="tbl",
        existing_column_names=existing,
        incoming_schema=incoming,
        allow_drop_columns=True,
    )
    assert result.has_drift is True
    assert "old_col" in result.dropped_columns
    drop_ddl = " ".join(result.ddl_statements)
    assert "DROP COLUMN" in drop_ddl
    assert "old_col" in drop_ddl


def test_schema_evolution_no_drop_without_flag():
    """verify_and_plan default (allow_drop_columns=False) tidak boleh generate DROP COLUMN."""
    incoming = TableSchema(name="tbl", columns=[
        ColumnDefinition(name="id", data_type=DataType.INTEGER),
    ])
    existing = ["id", "extra_col"]
    result = SchemaEvolutionVerifier.verify_and_plan(
        dialect="mysql",
        table_name="tbl",
        existing_column_names=existing,
        incoming_schema=incoming,
    )
    # Tidak ada drift dan tidak ada DROP DDL
    assert result.has_drift is False
    assert result.dropped_columns == []
    assert all("DROP" not in ddl.upper() for ddl in result.ddl_statements)


def test_schema_evolution_no_drop_for_sqlite_mirror():
    """verify_and_plan SQLite dengan allow_drop_columns=True tidak generate DROP (tidak didukung SQLite)."""
    incoming = TableSchema(name="tbl", columns=[
        ColumnDefinition(name="id", data_type=DataType.INTEGER),
    ])
    existing = ["id", "orphan"]
    result = SchemaEvolutionVerifier.verify_and_plan(
        dialect="sqlite",
        table_name="tbl",
        existing_column_names=existing,
        incoming_schema=incoming,
        allow_drop_columns=True,
    )
    # SQLite: tidak generate DROP DDL meski allow_drop_columns=True
    assert all("DROP" not in ddl.upper() for ddl in result.ddl_statements)
