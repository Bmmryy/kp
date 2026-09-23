"""Unit tests for SQL Base, MySQL, and PostgreSQL connectors.

Strategy: All tests use SQLAlchemy in-memory SQLite database to exercise
the SQLAlchemy-based base code WITHOUT requiring running MySQL/PostgreSQL
servers. Integration tests (requiring Docker) are in tests/integration/.

Tested:
  - URL construction (masked in logs)
  - _quote_identifier() per dialect
  - _generate_ddl() produces correct DDL for each dialect
  - get_schema() via SQLAlchemy Inspector
  - extract() yields Dataset chunks
  - create_schema() with if_exists modes (fail, replace, append, truncate)
  - load() inserts rows and returns count
  - Error translation: OperationalError → ConnectionFailedError
  - Password masking in URL strings
  - ConnectorRegistry has mysql and postgresql registered
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy import text

from app.connectors.base import ConnectorConfig
from app.connectors.mysql import MySQLDestination, MySQLSource
from app.connectors.postgresql import PostgreSQLDestination, PostgreSQLSource
from app.connectors.registry import ConnectorRegistry
from app.connectors.sql_base import _mask_url, SQLBaseDestination, SQLBaseSource
from app.core.exceptions import ConnectionFailedError, LoadError
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema


# ---------------------------------------------------------------------------
# Helpers — create concrete subclasses backed by in-memory SQLite for testing
# ---------------------------------------------------------------------------


class _SQLiteBackedSource(SQLBaseSource):
    """Test subclass that uses in-memory SQLite instead of real MySQL/PG."""

    def __init__(self, dialect_name: str = "sqlite") -> None:
        config = ConnectorConfig(name=f"test_{dialect_name}_src", connector_type=dialect_name, options={})
        super().__init__(config)
        self._dialect_name = dialect_name
        self._url = "sqlite+pysqlite://"  # in-memory

    @property
    def dialect(self) -> str:
        return self._dialect_name

    def _build_url(self) -> str:
        return self._url

    def _quote_identifier(self, name: str) -> str:
        return f'"{name}"'


class _SQLiteBackedDestination(SQLBaseDestination):
    """Test subclass that uses in-memory SQLite instead of real MySQL/PG."""

    def __init__(self, dialect_name: str = "sqlite") -> None:
        config = ConnectorConfig(name=f"test_{dialect_name}_dst", connector_type=dialect_name, options={})
        super().__init__(config)
        self._dialect_name = dialect_name
        self._url = "sqlite+pysqlite://"

    @property
    def dialect(self) -> str:
        return self._dialect_name

    def _build_url(self) -> str:
        return self._url

    def _quote_identifier(self, name: str) -> str:
        return f'"{name}"'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_schema() -> TableSchema:
    """Minimal schema: patient_id (INTEGER PK), name (STRING), active (BOOLEAN)."""
    return TableSchema(
        name="patients",
        columns=[
            ColumnDefinition(name="patient_id", data_type=DataType.INTEGER, nullable=False, primary_key=True),
            ColumnDefinition(name="name", data_type=DataType.STRING, nullable=False),
            ColumnDefinition(name="active", data_type=DataType.BOOLEAN, nullable=True),
        ],
    )


@pytest.fixture
def simple_dataset(simple_schema) -> Dataset:
    return Dataset(
        schema=simple_schema,
        rows=[
            {"patient_id": 1, "name": "Alice", "active": True},
            {"patient_id": 2, "name": "Bob", "active": False},
            {"patient_id": 3, "name": "Charlie", "active": True},
        ],
    )


@pytest.fixture
def source_with_data(simple_schema, simple_dataset) -> _SQLiteBackedSource:
    """Source connector backed by in-memory SQLite pre-populated with 3 rows."""
    src = _SQLiteBackedSource(dialect_name="sqlite")
    src.connect()
    # Manually create the table and insert data via SQLAlchemy
    with src._engine.begin() as conn:
        conn.execute(text(
            'CREATE TABLE "patients" ('
            '"patient_id" INTEGER PRIMARY KEY NOT NULL, '
            '"name" TEXT NOT NULL, '
            '"active" INTEGER)'
        ))
        conn.execute(text(
            'INSERT INTO "patients" VALUES (:patient_id, :name, :active)'
        ), simple_dataset.rows)
    return src


@pytest.fixture
def destination() -> _SQLiteBackedDestination:
    """Empty in-memory SQLite destination."""
    dst = _SQLiteBackedDestination(dialect_name="sqlite")
    dst.connect()
    return dst


# ---------------------------------------------------------------------------
# 1. URL Masking
# ---------------------------------------------------------------------------


class TestPasswordMasking:
    def test_mask_url_hides_password(self):
        url = "mysql+pymysql://root:supersecret@localhost:3306/mydb"
        masked = _mask_url(url)
        assert "supersecret" not in masked
        assert "***" in masked
        assert "root" in masked
        assert "localhost" in masked

    def test_mask_url_no_password_unchanged(self):
        url = "sqlite:///./test.db"
        assert _mask_url(url) == url

    def test_mask_url_special_chars_in_password(self):
        url = "postgresql+psycopg://user:p%40ssw0rd!@host:5432/db"
        masked = _mask_url(url)
        assert "p%40ssw0rd!" not in masked
        assert "***" in masked


# ---------------------------------------------------------------------------
# 2. MySQL — URL Construction and Identifier Quoting
# ---------------------------------------------------------------------------


class TestMySQLConnector:
    def _make_source(self, **opts) -> MySQLSource:
        config = ConnectorConfig(name="test_mysql_src", connector_type="mysql", options={
            "host": "localhost", "port": 3306,
            "database": "hospital_db", "user": "root",
            "password": "secret", **opts,
        })
        return MySQLSource(config)

    def _make_dest(self, **opts) -> MySQLDestination:
        config = ConnectorConfig(name="test_mysql_dst", connector_type="mysql", options={
            "host": "db.example.com", "port": 3306,
            "database": "hospital_db", "user": "etl_user",
            "password": "pa$$word", **opts,
        })
        return MySQLDestination(config)

    def test_mysql_source_url_format(self):
        src = self._make_source()
        url = src._build_url()
        assert url.startswith("mysql+pymysql://")
        assert "localhost:3306" in url
        assert "hospital_db" in url
        assert "charset=utf8mb4" in url

    def test_mysql_source_url_custom_port(self):
        src = self._make_source(port=3307)
        assert ":3307/" in src._build_url()

    def test_mysql_source_dialect(self):
        src = self._make_source()
        assert src.dialect == "mysql"

    def test_mysql_destination_url_format(self):
        dst = self._make_dest()
        url = dst._build_url()
        assert url.startswith("mysql+pymysql://")
        assert "db.example.com:3306" in url

    def test_mysql_destination_dialect(self):
        dst = self._make_dest()
        assert dst.dialect == "mysql"

    def test_mysql_backtick_quoting(self):
        src = self._make_source()
        assert src._quote_identifier("my table") == "`my table`"
        dst = self._make_dest()
        assert dst._quote_identifier("col name") == "`col name`"


# ---------------------------------------------------------------------------
# 3. PostgreSQL — URL Construction and Identifier Quoting
# ---------------------------------------------------------------------------


class TestPostgreSQLConnector:
    def _make_source(self, **opts) -> PostgreSQLSource:
        config = ConnectorConfig(name="test_pg_src", connector_type="postgresql", options={
            "host": "localhost", "port": 5432,
            "database": "hospital_dw", "user": "postgres",
            "password": "pgpass", **opts,
        })
        return PostgreSQLSource(config)

    def _make_dest(self, **opts) -> PostgreSQLDestination:
        config = ConnectorConfig(name="test_pg_dst", connector_type="postgresql", options={
            "host": "pg.example.com", "port": 5432,
            "database": "hospital_dw", "user": "etl_user",
            "password": "securepass", **opts,
        })
        return PostgreSQLDestination(config)

    def test_pg_source_url_format(self):
        src = self._make_source()
        url = src._build_url()
        assert url.startswith("postgresql+psycopg://")
        assert "localhost:5432" in url
        assert "hospital_dw" in url

    def test_pg_source_dialect(self):
        src = self._make_source()
        assert src.dialect == "postgresql"

    def test_pg_destination_url_format(self):
        dst = self._make_dest()
        url = dst._build_url()
        assert "pg.example.com:5432" in url

    def test_pg_double_quote_identifier(self):
        src = self._make_source()
        assert src._quote_identifier("my col") == '"my col"'
        dst = self._make_dest()
        assert dst._quote_identifier("table name") == '"table name"'


# ---------------------------------------------------------------------------
# 4. DDL Generation via SQLBaseDestination._generate_ddl()
# ---------------------------------------------------------------------------


class TestDDLGeneration:
    def _dest(self, dialect: str) -> _SQLiteBackedDestination:
        dst = _SQLiteBackedDestination(dialect_name=dialect)
        return dst

    def test_ddl_sqlite_types(self, simple_schema):
        dst = self._dest("sqlite")
        ddl = dst._generate_ddl(simple_schema)
        assert "CREATE TABLE" in ddl
        assert '"patients"' in ddl
        assert "INTEGER" in ddl
        assert "PRIMARY KEY" in ddl
        assert "NOT NULL" in ddl

    def test_ddl_mysql_types(self, simple_schema):
        dst = self._dest("mysql")
        ddl = dst._generate_ddl(simple_schema)
        # MySQL target for BOOLEAN is TINYINT(1)
        assert "TINYINT(1)" in ddl
        # MySQL target for STRING is VARCHAR(255)
        assert "VARCHAR(255)" in ddl
        # MySQL target for INTEGER is INT
        assert " INT " in ddl or ddl.endswith(" INT")

    def test_ddl_postgresql_types(self, simple_schema):
        dst = self._dest("postgresql")
        ddl = dst._generate_ddl(simple_schema)
        # PostgreSQL target for BOOLEAN is BOOLEAN
        assert "BOOLEAN" in ddl
        # PostgreSQL target for STRING is VARCHAR(255)
        assert "VARCHAR(255)" in ddl

    def test_ddl_column_order_preserved(self, simple_schema):
        dst = self._dest("sqlite")
        ddl = dst._generate_ddl(simple_schema)
        idx_id = ddl.index("patient_id")
        idx_name = ddl.index("name")
        idx_active = ddl.index("active")
        assert idx_id < idx_name < idx_active


# ---------------------------------------------------------------------------
# 5. Schema Discovery (get_schema) via SQLAlchemy Inspector
# ---------------------------------------------------------------------------


class TestSchemaDiscovery:
    def test_get_schema_returns_correct_columns(self, source_with_data):
        schema = source_with_data.get_schema("patients")
        assert schema.name == "patients"
        col_names = [c.name for c in schema.columns]
        assert "patient_id" in col_names
        assert "name" in col_names
        assert "active" in col_names

    def test_get_schema_nonexistent_table_raises(self, source_with_data):
        from app.core.exceptions import SchemaDiscoveryError
        with pytest.raises(SchemaDiscoveryError):
            source_with_data.get_schema("nonexistent_table_xyz")

    def test_list_tables_returns_patients(self, source_with_data):
        tables = source_with_data.list_tables()
        assert "patients" in tables


# ---------------------------------------------------------------------------
# 6. Extraction — chunked iteration
# ---------------------------------------------------------------------------


class TestExtraction:
    def test_extract_yields_all_rows(self, source_with_data, simple_schema):
        all_rows = []
        for dataset in source_with_data.extract("patients"):
            assert isinstance(dataset, Dataset)
            all_rows.extend(dataset.rows)
        assert len(all_rows) == 3

    def test_extract_with_small_chunk_size(self, source_with_data):
        chunks = list(source_with_data.extract("patients", chunk_size=1))
        # 3 rows, chunk_size=1 → 3 datasets
        assert len(chunks) == 3
        for chunk in chunks:
            assert len(chunk.rows) == 1

    def test_extract_with_custom_query(self, source_with_data, simple_schema):
        datasets = list(source_with_data.extract(
            "patients",
            query='SELECT * FROM "patients" WHERE "patient_id" = 1',
        ))
        all_rows = [row for ds in datasets for row in ds.rows]
        assert len(all_rows) == 1
        assert all_rows[0]["patient_id"] == 1


# ---------------------------------------------------------------------------
# 7. create_schema — if_exists modes
# ---------------------------------------------------------------------------


class TestCreateSchema:
    def test_create_schema_new_table(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        insp = sa.inspect(destination._engine)
        assert insp.has_table("patients")

    def test_create_schema_fail_on_existing(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        with pytest.raises(LoadError):
            destination.create_schema(simple_schema, if_exists="fail")

    def test_create_schema_replace(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        # Should not raise; drops and recreates
        destination.create_schema(simple_schema, if_exists="replace")
        insp = sa.inspect(destination._engine)
        assert insp.has_table("patients")

    def test_create_schema_append_does_not_recreate(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        # Insert a sentinel row
        with destination._engine.begin() as conn:
            conn.execute(text(
                'INSERT INTO "patients" ("patient_id","name","active") VALUES (99,"sentinel",1)'
            ))
        # append mode should leave existing data intact
        destination.create_schema(simple_schema, if_exists="append")
        with destination._engine.connect() as conn:
            row_count = conn.execute(text('SELECT COUNT(*) FROM "patients"')).scalar()
        assert row_count == 1

    def test_create_schema_truncate_clears_rows(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        with destination._engine.begin() as conn:
            conn.execute(text(
                'INSERT INTO "patients" ("patient_id","name","active") VALUES (99,"sentinel",1)'
            ))
        destination.create_schema(simple_schema, if_exists="truncate")
        with destination._engine.connect() as conn:
            row_count = conn.execute(text('SELECT COUNT(*) FROM "patients"')).scalar()
        assert row_count == 0


# ---------------------------------------------------------------------------
# 8. load() — row insertion
# ---------------------------------------------------------------------------


class TestLoad:
    def test_load_returns_row_count(self, destination, simple_schema, simple_dataset):
        destination.create_schema(simple_schema, if_exists="fail")
        count = destination.load(simple_dataset, "patients")
        assert count == 3

    def test_load_data_persisted(self, destination, simple_schema, simple_dataset):
        destination.create_schema(simple_schema, if_exists="fail")
        destination.load(simple_dataset, "patients")
        with destination._engine.connect() as conn:
            rows = conn.execute(text('SELECT * FROM "patients" ORDER BY "patient_id"')).fetchall()
        assert len(rows) == 3
        assert rows[0][0] == 1   # patient_id
        assert rows[1][1] == "Bob"  # name

    def test_load_empty_dataset_returns_zero(self, destination, simple_schema):
        destination.create_schema(simple_schema, if_exists="fail")
        empty = Dataset(schema=simple_schema, rows=[])
        count = destination.load(empty, "patients")
        assert count == 0

    def test_load_multiple_batches(self, destination, simple_schema, simple_dataset):
        destination.create_schema(simple_schema, if_exists="fail")
        # Load twice → 6 rows total (append mode)
        destination.load(simple_dataset, "patients")
        # Need different PKs for second batch
        batch2 = Dataset(schema=simple_schema, rows=[
            {"patient_id": 4, "name": "Diana", "active": True},
            {"patient_id": 5, "name": "Eve", "active": False},
        ])
        destination.load(batch2, "patients")
        with destination._engine.connect() as conn:
            count = conn.execute(text('SELECT COUNT(*) FROM "patients"')).scalar()
        assert count == 5


# ---------------------------------------------------------------------------
# 9. Error Translation
# ---------------------------------------------------------------------------


class TestErrorTranslation:
    def test_connection_failed_bad_url(self):
        """Connecting to a non-existent host raises ConnectionFailedError."""
        class _BadURLSource(SQLBaseSource):
            @property
            def dialect(self):
                return "mysql"

            def _build_url(self):
                # Invalid host guaranteed to fail
                return "mysql+pymysql://nouser:nopass@127.0.0.1:19999/nodb"

            def _quote_identifier(self, name):
                return f"`{name}`"

        src = _BadURLSource(ConnectorConfig(name="test_bad_url", connector_type="mysql", options={}))
        with pytest.raises(ConnectionFailedError):
            src.connect()


# ---------------------------------------------------------------------------
# 10. ConnectorRegistry — mysql and postgresql are registered
# ---------------------------------------------------------------------------


class TestConnectorRegistration:
    def test_mysql_source_registered(self):
        # Import triggers _register_builtin_connectors()
        import app.connectors  # noqa: F401
        src_cls = ConnectorRegistry.get_source_class("mysql")
        from app.connectors.mysql import MySQLSource
        assert src_cls is MySQLSource

    def test_mysql_destination_registered(self):
        import app.connectors  # noqa: F401
        dst_cls = ConnectorRegistry.get_destination_class("mysql")
        from app.connectors.mysql import MySQLDestination
        assert dst_cls is MySQLDestination

    def test_postgresql_source_registered(self):
        import app.connectors  # noqa: F401
        src_cls = ConnectorRegistry.get_source_class("postgresql")
        from app.connectors.postgresql import PostgreSQLSource
        assert src_cls is PostgreSQLSource

    def test_postgresql_destination_registered(self):
        import app.connectors  # noqa: F401
        dst_cls = ConnectorRegistry.get_destination_class("postgresql")
        from app.connectors.postgresql import PostgreSQLDestination
        assert dst_cls is PostgreSQLDestination

    def test_postgres_alias_registered(self):
        import app.connectors  # noqa: F401
        # 'postgres' alias should resolve to same class as 'postgresql'
        src_cls = ConnectorRegistry.get_source_class("postgres")
        from app.connectors.postgresql import PostgreSQLSource
        assert src_cls is PostgreSQLSource
