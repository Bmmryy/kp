"""FlowETL PostgreSQL Source and Destination Connectors.

Provides PostgreSQL-specific connector implementations built on top of the shared
SQLAlchemy base (sql_base.py).

Connection driver: psycopg 3 (modern binary driver)
Connection URL format: postgresql+psycopg://{user}:{password}@{host}:{port}/{database}
Identifier quoting: double-quote ("name")
Dialect key: "postgresql" (matches TypeRegistry)

Usage in pipeline YAML::

    destination:
      type: postgresql
      options:
        host: localhost
        port: 5432
        database: hospital_dw
        user: postgres
        password: "${PG_PASSWORD}"
        table: dim_patients
"""

from __future__ import annotations

from typing import Optional

from app.connectors.base import ConnectorConfig
from app.connectors.sql_base import SQLBaseDestination, SQLBaseSource


class PostgreSQLSource(SQLBaseSource):
    """Source connector for extracting data from PostgreSQL databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 5432))
        self._database: str = opts.get("database", "")
        self._user: str = opts.get("user", "postgres")
        self._password: str = opts.get("password", "")
        # Optional: schema search path (default public)
        self._schema: str = opts.get("schema", "public")

    @property
    def dialect(self) -> str:
        return "postgresql"

    def _build_url(self) -> str:
        return (
            f"postgresql+psycopg://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/{self._database}"
        )

    def _quote_identifier(self, name: str) -> str:
        """PostgreSQL uses ANSI double-quote quoting."""
        return f'"{name}"'


class PostgreSQLDestination(SQLBaseDestination):
    """Destination connector for loading data into PostgreSQL databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 5432))
        self._database: str = opts.get("database", "")
        self._user: str = opts.get("user", "postgres")
        self._password: str = opts.get("password", "")
        self._schema: str = opts.get("schema", "public")

    @property
    def dialect(self) -> str:
        return "postgresql"

    def _build_url(self) -> str:
        return (
            f"postgresql+psycopg://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/{self._database}"
        )

    def _quote_identifier(self, name: str) -> str:
        """PostgreSQL uses ANSI double-quote quoting."""
        return f'"{name}"'
