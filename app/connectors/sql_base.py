"""FlowETL SQL Base Connector — Shared SQLAlchemy 2.0 Foundation.

All relational database connectors (MySQL, PostgreSQL, SQL Server, etc.) inherit
from SQLBaseSource and SQLBaseDestination defined here. This module:

  - Abstracts connection management via SQLAlchemy engine
  - Provides schema discovery via SQLAlchemy Inspector
  - Implements server-side streaming extraction
  - Handles transactional batch inserts
  - Wraps all SQLAlchemy exceptions into FlowETL error hierarchy
  - Masks passwords in log messages

Subclasses only need to override:
  - ``dialect`` property → dialect name for TypeRegistry (e.g., "mysql")
  - ``_build_url()`` → return SQLAlchemy-compatible connection URL string
  - ``_quote_identifier()`` → dialect-specific quoting (backtick vs double-quote)
"""

from __future__ import annotations

import re
from abc import abstractmethod
from typing import Any, Dict, Iterator, List, Optional, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.exc import (
    OperationalError,
    ProgrammingError,
    NoSuchTableError,
    SQLAlchemyError,
)

from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.exceptions import (
    ConnectionFailedError,
    ExtractionError,
    LoadError,
    SchemaDiscoveryError,
)
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from app.schema.evolution import SchemaEvolutionVerifier
from app.utils.logging import get_logger

logger = get_logger("flowetl.connectors.sql_base")

# Regex to mask passwords in SQLAlchemy URLs
# Matches :password@ in urls like dialect://user:password@host
_PASSWORD_MASK_RE = re.compile(r"(://[^:]+:)([^@]+)(@)")


def _mask_url(url: str) -> str:
    """Return connection URL with password replaced by '***'."""
    return _PASSWORD_MASK_RE.sub(r"\1***\3", url)


class SQLBaseSource(SourceConnector):
    """Generic relational database source connector using SQLAlchemy 2.0.

    Subclasses must implement ``dialect``, ``_build_url()``, and
    ``_quote_identifier()``.
    """

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._engine: Optional[sa.Engine] = None
        self._inspector: Optional[Any] = None  # sqlalchemy.Inspector

    # ------------------------------------------------------------------
    # Abstract interface for subclasses
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def dialect(self) -> str:
        """Return the dialect name used for TypeRegistry lookup (e.g. 'mysql')."""

    @abstractmethod
    def _build_url(self) -> str:
        """Return a fully-formed SQLAlchemy connection URL string."""

    def _quote_identifier(self, name: str) -> str:
        """Quote an identifier (column/table name). Default: ANSI double-quote."""
        return f'"{name}"'

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        url = self._build_url()
        masked = _mask_url(url)
        logger.info("Connecting to %s: %s", self.dialect, masked)
        try:
            self._engine = sa.create_engine(url, pool_pre_ping=True)
            # Eagerly verify reachability
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._inspector = sa_inspect(self._engine)
            self._is_connected = True
            logger.info("Connected to %s successfully.", self.dialect)
        except OperationalError as err:
            raise ConnectionFailedError(
                message=f"Cannot connect to {self.dialect} at {masked}: {err.orig}",
                details=str(err),
                suggested_action=(
                    "Verify host, port, credentials, and that the database server "
                    "is running and accessible."
                ),
            ) from err
        except SQLAlchemyError as err:
            raise ConnectionFailedError(
                message=f"Unexpected error connecting to {self.dialect}: {err}",
                details=str(err),
            ) from err

    def test_connection(self) -> bool:
        self.connect()
        with self._engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None

    def close(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._inspector = None
        self._is_connected = False

    # ------------------------------------------------------------------
    # Schema discovery
    # ------------------------------------------------------------------

    def list_tables(self) -> List[str]:
        if not self.is_connected or not self._inspector:
            self.connect()
        try:
            return self._inspector.get_table_names()
        except SQLAlchemyError as err:
            raise SchemaDiscoveryError(
                message=f"Failed to list tables in {self.dialect}: {err}",
                details=str(err),
            ) from err

    def get_schema(self, table_name: str) -> TableSchema:
        if not self.is_connected or not self._inspector:
            self.connect()
        try:
            col_infos = self._inspector.get_columns(table_name)
        except NoSuchTableError:
            available = self.list_tables()
            raise SchemaDiscoveryError(
                message=f"Table '{table_name}' does not exist in {self.dialect} database.",
                suggested_action=f"Available tables: {available}",
            )
        except SQLAlchemyError as err:
            raise SchemaDiscoveryError(
                message=f"Failed to inspect table '{table_name}' in {self.dialect}: {err}",
                details=str(err),
            ) from err

        # Retrieve primary key columns
        try:
            pk_info = self._inspector.get_pk_constraint(table_name)
            pk_cols: set[str] = set(pk_info.get("constrained_columns", []))
        except SQLAlchemyError:
            pk_cols = set()

        columns: List[ColumnDefinition] = []
        for col in col_infos:
            col_name: str = col["name"]
            # SQLAlchemy type object → string repr (e.g. "VARCHAR(255)")
            raw_type: str = str(col["type"])
            nullable: bool = col.get("nullable", True)
            default = col.get("default")

            canonical = TypeRegistry.to_canonical(self.dialect, raw_type)
            columns.append(
                ColumnDefinition(
                    name=col_name,
                    data_type=canonical,
                    nullable=nullable,
                    primary_key=(col_name in pk_cols),
                    default=default,
                )
            )

        return TableSchema(name=table_name, columns=columns)

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        if not self.is_connected or not self._engine:
            self.connect()

        schema = self.get_schema(table_name)
        sql = query or f"SELECT * FROM {self._quote_identifier(table_name)}"
        effective_chunk = chunk_size or 5000

        logger.info(
            "Extracting from %s table '%s' with chunk_size=%d",
            self.dialect,
            table_name,
            effective_chunk,
        )
        try:
            with self._engine.connect() as conn:
                # stream_results enables server-side cursors where supported
                result = conn.execution_options(stream_results=True).execute(
                    text(sql)
                )
                col_keys = list(result.keys())
                while True:
                    rows = result.fetchmany(effective_chunk)
                    if not rows:
                        break
                    records = [dict(zip(col_keys, row)) for row in rows]
                    yield Dataset(schema=schema, rows=records)
        except ExtractionError:
            raise
        except SQLAlchemyError as err:
            raise ExtractionError(
                message=f"Extraction from {self.dialect} table '{table_name}' failed: {err}",
                details=str(err),
            ) from err


class SQLBaseDestination(DestinationConnector):
    """Generic relational database destination connector using SQLAlchemy 2.0.

    Subclasses must implement ``dialect``, ``_build_url()``, and
    ``_quote_identifier()``.
    """

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._engine: Optional[sa.Engine] = None

    # ------------------------------------------------------------------
    # Abstract interface for subclasses
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def dialect(self) -> str:
        """Return the dialect name used for TypeRegistry lookup."""

    @abstractmethod
    def _build_url(self) -> str:
        """Return a fully-formed SQLAlchemy connection URL string."""

    def _quote_identifier(self, name: str) -> str:
        """Quote an identifier. Default: ANSI double-quote."""
        return f'"{name}"'

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        url = self._build_url()
        masked = _mask_url(url)
        logger.info("Connecting to %s destination: %s", self.dialect, masked)
        try:
            self._engine = sa.create_engine(url, pool_pre_ping=True)
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._is_connected = True
            logger.info("Connected to %s destination successfully.", self.dialect)
        except OperationalError as err:
            raise ConnectionFailedError(
                message=f"Cannot connect to {self.dialect} destination at {masked}: {err.orig}",
                details=str(err),
                suggested_action=(
                    "Verify host, port, credentials, and that the database server is running."
                ),
            ) from err
        except SQLAlchemyError as err:
            raise ConnectionFailedError(
                message=f"Unexpected error connecting to {self.dialect} destination: {err}",
                details=str(err),
            ) from err

    def test_connection(self) -> bool:
        self.connect()
        with self._engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None

    def close(self) -> None:
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._is_connected = False

    # ------------------------------------------------------------------
    # Schema Management
    # ------------------------------------------------------------------

    def _generate_ddl(self, schema: TableSchema) -> str:
        """Generate a CREATE TABLE DDL statement for the target dialect."""
        col_defs: List[str] = []
        for col in schema.columns:
            native_type = TypeRegistry.to_native(
                self.dialect,
                col.data_type,
                # ColumnDefinition does not carry dimension overrides;
                # TypeRegistry defaults (e.g. VARCHAR(255)) are used as-is.
                length=None,
                precision=None,
                scale=None,
            )
            q = self._quote_identifier(col.name)
            constraints: List[str] = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if not col.nullable:
                constraints.append("NOT NULL")
            c_str = f" {' '.join(constraints)}" if constraints else ""
            col_defs.append(f"  {q} {native_type}{c_str}")

        body = ",\n".join(col_defs)
        qt = self._quote_identifier(schema.name)
        return f"CREATE TABLE {qt} (\n{body}\n)"

    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        if not self.is_connected or not self._engine:
            self.connect()

        insp = sa_inspect(self._engine)
        table_exists = insp.has_table(schema.name)
        qt = self._quote_identifier(schema.name)

        try:
            with self._engine.begin() as conn:
                if table_exists:
                    if if_exists == "fail":
                        raise LoadError(
                            message=f"Target table '{schema.name}' already exists in {self.dialect}.",
                            suggested_action="Use mode 'replace' or 'append'.",
                        )
                    elif if_exists == "replace":
                        conn.execute(text(f"DROP TABLE IF EXISTS {qt}"))
                        table_exists = False
                    elif if_exists == "truncate":
                        conn.execute(text(f"DELETE FROM {qt}"))
                        return
                    elif if_exists == "append":
                        # Verified Schema Evolution: check for drift & auto-alter target
                        existing_cols = [c["name"] for c in insp.get_columns(schema.name)]
                        evo = SchemaEvolutionVerifier.verify_and_plan(
                            dialect=self.dialect,
                            table_name=schema.name,
                            existing_column_names=existing_cols,
                            incoming_schema=schema,
                            quote_fn=self._quote_identifier,
                        )
                        if evo.has_drift:
                            for ddl_stmt in evo.ddl_statements:
                                logger.info(
                                    "Executing Verified Schema Evolution on %s:\n%s",
                                    self.dialect,
                                    ddl_stmt,
                                )
                                conn.execute(text(ddl_stmt))
                        return

                if not table_exists:
                    ddl = self._generate_ddl(schema)
                    logger.info("Creating table in %s:\n%s", self.dialect, ddl)
                    conn.execute(text(ddl))
        except LoadError:
            raise
        except SQLAlchemyError as err:
            raise LoadError(
                message=f"Failed to create table '{schema.name}' in {self.dialect}: {err}",
                details=str(err),
            ) from err

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, dataset: Dataset, table_name: str, mode: str = "append") -> int:
        if not self.is_connected or not self._engine:
            self.connect()

        if not dataset.rows:
            return 0

        qt = self._quote_identifier(table_name)
        cols = dataset.schema_def.column_names
        q_cols = ", ".join(self._quote_identifier(c) for c in cols)
        placeholders = ", ".join(f":{c}" for c in cols)
        insert_sql = f"INSERT INTO {qt} ({q_cols}) VALUES ({placeholders})"

        logger.debug(
            "Loading %d rows into %s table '%s' (mode=%s)",
            len(dataset.rows),
            self.dialect,
            table_name,
            mode,
        )

        try:
            with self._engine.begin() as conn:
                conn.execute(text(insert_sql), dataset.rows)
            return len(dataset.rows)
        except SQLAlchemyError as err:
            raise LoadError(
                message=f"Failed to insert records into {self.dialect} table '{table_name}': {err}",
                details=str(err),
            ) from err
