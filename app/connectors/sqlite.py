"""FlowETL SQLite Relational Source and Destination Connectors.

Provides a full SQL engine connector using Python's built-in sqlite3 database,
supporting DDL schema generation via TypeRegistry, schema reflection,
and chunked extraction.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterator, List, Optional

from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.exceptions import (
    ConnectionFailedError,
    ExtractionError,
    LoadError,
    SchemaDiscoveryError,
)
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from app.utils.logging import get_logger

logger = get_logger("flowetl.connectors.sqlite")


class SQLiteSource(SourceConnector):
    """Source connector for querying and extracting tables from SQLite databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.database_path = config.options.get("database", ":memory:")
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self.database_path != ":memory:":
            db_file = Path(self.database_path)
            if not db_file.exists():
                raise ConnectionFailedError(
                    message=f"SQLite database file does not exist: {db_file.resolve()}",
                    suggested_action="Verify the 'database' path in your connection options.",
                )
        try:
            self._conn = sqlite3.connect(self.database_path)
            self._conn.row_factory = sqlite3.Row
            self._is_connected = True
        except Exception as err:
            raise ConnectionFailedError(
                message=f"Failed to connect to SQLite database '{self.database_path}': {err}",
                details=str(err),
            ) from err

    def test_connection(self) -> bool:
        self.connect()
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1;")
        return cursor.fetchone() is not None

    def list_tables(self) -> List[str]:
        if not self.is_connected or not self._conn:
            self.connect()
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        return [row[0] for row in cursor.fetchall()]

    def get_schema(self, table_name: str) -> TableSchema:
        if not self.is_connected or not self._conn:
            self.connect()
        cursor = self._conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        rows = cursor.fetchall()
        if not rows:
            raise SchemaDiscoveryError(
                message=f"Table '{table_name}' does not exist in SQLite database.",
                suggested_action=f"Available tables: {self.list_tables()}",
            )

        columns: List[ColumnDefinition] = []
        for r in rows:
            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            col_name = r["name"]
            raw_type = r["type"] or "TEXT"
            not_null = bool(r["notnull"])
            is_pk = bool(r["pk"])
            default_val = r["dflt_value"]

            canonical_type = TypeRegistry.to_canonical("sqlite", raw_type)
            columns.append(
                ColumnDefinition(
                    name=col_name,
                    data_type=canonical_type,
                    nullable=not not_null,
                    primary_key=is_pk,
                    default=default_val,
                )
            )

        return TableSchema(name=table_name, columns=columns)

    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        if not self.is_connected or not self._conn:
            self.connect()

        schema = self.get_schema(table_name)
        sql = query or f"SELECT * FROM {table_name}"
        effective_chunk_size = chunk_size or 5000

        try:
            cursor = self._conn.cursor()
            cursor.execute(sql)
            while True:
                rows = cursor.fetchmany(effective_chunk_size)
                if not rows:
                    break
                records = [dict(r) for r in rows]
                yield Dataset(schema=schema, rows=records)
        except Exception as err:
            raise ExtractionError(
                message=f"Failed to execute extraction query on SQLite table '{table_name}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
        self._is_connected = False


class SQLiteDestination(DestinationConnector):
    """Destination connector for creating schemas and loading records into SQLite."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.database_path = config.options.get("database", ":memory:")
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self.database_path != ":memory:":
            db_file = Path(self.database_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._conn = sqlite3.connect(self.database_path)
            self._is_connected = True
        except Exception as err:
            raise ConnectionFailedError(
                message=f"Failed to connect to SQLite destination '{self.database_path}': {err}",
                details=str(err),
            ) from err

    def test_connection(self) -> bool:
        self.connect()
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1;")
        return cursor.fetchone() is not None

    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        if not self.is_connected or not self._conn:
            self.connect()

        cursor = self._conn.cursor()
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (schema.name,))
        table_exists = cursor.fetchone() is not None

        if table_exists:
            if if_exists == "fail":
                raise LoadError(
                    message=f"Target SQLite table '{schema.name}' already exists.",
                    suggested_action="Specify mode 'replace' or 'append'.",
                )
            elif if_exists == "replace":
                cursor.execute(f"DROP TABLE IF EXISTS {schema.name}")
            elif if_exists in ("append", "truncate", "sync", "mirror"):
                from app.schema.evolution import SchemaEvolutionVerifier
                cursor.execute(f"PRAGMA table_info({schema.name})")
                existing_cols = [r[1] for r in cursor.fetchall()]
                evo = SchemaEvolutionVerifier.verify_and_plan(
                    dialect="sqlite",
                    table_name=schema.name,
                    existing_column_names=existing_cols,
                    incoming_schema=schema,
                    quote_fn=lambda n: f'"{n}"',
                )
                if evo.has_drift:
                    for ddl_stmt in evo.ddl_statements:
                        cursor.execute(ddl_stmt)
                    self._conn.commit()
                if if_exists in ("truncate", "sync", "mirror"):
                    cursor.execute(f"DELETE FROM {schema.name}")
                    self._conn.commit()
                return

        # Generate DDL using TypeRegistry
        col_defs = []
        for col in schema.columns:
            sqlite_type = TypeRegistry.to_native("sqlite", col.data_type)
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if not col.nullable:
                constraints.append("NOT NULL")
            constraint_str = f" {' '.join(constraints)}" if constraints else ""
            col_defs.append(f'"{col.name}" {sqlite_type}{constraint_str}')

        ddl = f"CREATE TABLE IF NOT EXISTS {schema.name} (\n  " + ",\n  ".join(col_defs) + "\n);"
        try:
            cursor.execute(ddl)
            self._conn.commit()
        except Exception as err:
            raise LoadError(
                message=f"Failed to create SQLite table '{schema.name}': {err}",
                details=str(err),
            ) from err

    def load(
        self,
        dataset: Dataset,
        table_name: str,
        mode: str = "append",
    ) -> int:
        if not self.is_connected or not self._conn:
            self.connect()

        if not dataset.rows:
            return 0

        cursor = self._conn.cursor()
        cols = dataset.schema_def.column_names
        placeholders = ", ".join(["?"] * len(cols))
        col_names_quoted = ", ".join([f'"{c}"' for c in cols])
        insert_sql = f"INSERT INTO {table_name} ({col_names_quoted}) VALUES ({placeholders})"

        # Convert rows into tuples matching column order with Decimal coercion
        values = []
        for row in dataset.rows:
            row_vals = []
            for c in cols:
                v = row.get(c)
                if isinstance(v, Decimal):
                    v = float(v)
                row_vals.append(v)
            values.append(tuple(row_vals))

        try:
            cursor.executemany(insert_sql, values)
            self._conn.commit()
            return len(values)
        except Exception as err:
            raise LoadError(
                message=f"Failed to batch insert records into SQLite table '{table_name}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
        self._is_connected = False
