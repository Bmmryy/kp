"""FlowETL MySQL Source and Destination Connectors.

Provides MySQL-specific connector implementations built on top of the shared
SQLAlchemy base (sql_base.py).

Connection driver: PyMySQL (pure-Python, no binary dependency)
Connection URL format: mysql+pymysql://{user}:{password}@{host}:{port}/{database}
Identifier quoting: backtick (`name`)
Dialect key: "mysql" (matches TypeRegistry)

Usage in pipeline YAML::

    source:
      type: mysql
      options:
        host: localhost
        port: 3306
        database: hospital_db
        user: root
        password: "${MYSQL_PASSWORD}"
        table: patients
"""

from __future__ import annotations

from typing import Optional

from app.connectors.base import ConnectorConfig
from app.connectors.sql_base import SQLBaseDestination, SQLBaseSource


class MySQLSource(SQLBaseSource):
    """Source connector for extracting data from MySQL databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 3306))
        self._database: str = opts.get("database", "")
        self._user: str = opts.get("user", "root")
        self._password: str = opts.get("password", "")
        # Optional: connection charset (default utf8mb4 for full Unicode support)
        self._charset: str = opts.get("charset", "utf8mb4")

    @property
    def dialect(self) -> str:
        return "mysql"

    def _build_url(self) -> str:
        return (
            f"mysql+pymysql://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/{self._database}"
            f"?charset={self._charset}"
        )

    def _quote_identifier(self, name: str) -> str:
        """MySQL uses backtick quoting."""
        return f"`{name}`"


class MySQLDestination(SQLBaseDestination):
    """Destination connector for loading data into MySQL databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 3306))
        self._database: str = opts.get("database", "")
        self._user: str = opts.get("user", "root")
        self._password: str = opts.get("password", "")
        self._charset: str = opts.get("charset", "utf8mb4")

    @property
    def dialect(self) -> str:
        return "mysql"

    def _build_url(self) -> str:
        return (
            f"mysql+pymysql://{self._user}:{self._password}"
            f"@{self._host}:{self._port}/{self._database}"
            f"?charset={self._charset}"
        )

    def _quote_identifier(self, name: str) -> str:
        """MySQL uses backtick quoting."""
        return f"`{name}`"
