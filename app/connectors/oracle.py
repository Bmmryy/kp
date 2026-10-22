"""FlowETL Oracle Source and Destination Connectors.

Provides Oracle-specific connector implementations built on top of the shared
SQLAlchemy base (sql_base.py).

Connection driver: python-oracledb (pure-Python thin mode, no instant client required)
Connection URL format: oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}
Identifier quoting: double-quotes ("NAME")
Dialect key: "oracle" (matches TypeRegistry)

Usage in pipeline YAML::

    source:
      type: oracle
      options:
        host: localhost
        port: 1521
        database: FREEPDB1  # or service_name
        user: system
        password: "${ORACLE_PASSWORD}"
        table: PATIENTS
"""

from __future__ import annotations

from typing import Optional

from app.connectors.base import ConnectorConfig
from app.connectors.sql_base import SQLBaseDestination, SQLBaseSource


class OracleSource(SQLBaseSource):
    """Source connector for extracting data from Oracle databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 1521))
        # Support service_name or database or sid
        self._service_name: str = opts.get("service_name") or opts.get("database") or "FREEPDB1"
        self._sid: Optional[str] = opts.get("sid")
        self._user: str = opts.get("user", "system")
        self._password: str = opts.get("password", "")

    @property
    def dialect(self) -> str:
        return "oracle"

    def _build_url(self) -> str:
        if self._sid:
            return (
                f"oracle+oracledb://{self._user}:{self._password}"
                f"@{self._host}:{self._port}/{self._sid}"
            )
        return (
            f"oracle+oracledb://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/?service_name={self._service_name}"
        )

    def _quote_identifier(self, name: str) -> str:
        """Oracle uses double-quote identifier quoting."""
        escaped = name.replace('"', '""')
        return f'"{escaped}"'


class OracleDestination(SQLBaseDestination):
    """Destination connector for loading data into Oracle databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 1521))
        self._service_name: str = opts.get("service_name") or opts.get("database") or "FREEPDB1"
        self._sid: Optional[str] = opts.get("sid")
        self._user: str = opts.get("user", "system")
        self._password: str = opts.get("password", "")

    @property
    def dialect(self) -> str:
        return "oracle"

    def _build_url(self) -> str:
        if self._sid:
            return (
                f"oracle+oracledb://{self._user}:{self._password}"
                f"@{self._host}:{self._port}/{self._sid}"
            )
        return (
            f"oracle+oracledb://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/?service_name={self._service_name}"
        )

    def _quote_identifier(self, name: str) -> str:
        """Oracle uses double-quote identifier quoting."""
        escaped = name.replace('"', '""')
        return f'"{escaped}"'
