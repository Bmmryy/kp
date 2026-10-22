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
        service_name: FREEPDB1   # service name koneksi (tetap FREEPDB1)
        database: SYSTEM          # schema/owner di Oracle (default: sama dengan user)
        user: system
        password: "${ORACLE_PASSWORD}"
        table: HOSPITAL_PATIENTS
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
        # service_name = nama service Oracle (FREEPDB1), BUKAN schema
        # database = schema/owner (misal: SYSTEM, PDBADMIN)
        # Jika user set "database" berisi nama service, tetap pakai FREEPDB1
        raw_db = opts.get("database", "")
        raw_svc = opts.get("service_name", "")
        # Heuristik: jika database adalah service name yang dikenal, pakai sebagai service_name
        known_services = {"freepdb1", "xepdb1", "orclpdb1", "pdborcl", "orcl"}
        if raw_svc:
            self._service_name: str = raw_svc
            self._schema: Optional[str] = raw_db.upper() if raw_db else None
        elif raw_db.lower() in known_services:
            # user mengisi field "database" dengan service name (behavior lama)
            self._service_name = raw_db
            self._schema = None  # pakai default schema user
        else:
            self._service_name = "FREEPDB1"
            self._schema = raw_db.upper() if raw_db else None
        self._sid: Optional[str] = opts.get("sid")
        self._user: str = opts.get("user", "system").strip()
        self._password: str = opts.get("password", "").strip()

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

    def _get_schema(self) -> Optional[str]:
        """Kembalikan schema/owner yang dipakai untuk query tabel."""
        return self._schema


class OracleDestination(SQLBaseDestination):
    """Destination connector for loading data into Oracle databases."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        opts = config.options
        self._host: str = opts.get("host", "localhost")
        self._port: int = int(opts.get("port", 1521))
        raw_db = opts.get("database", "")
        raw_svc = opts.get("service_name", "")
        known_services = {"freepdb1", "xepdb1", "orclpdb1", "pdborcl", "orcl"}
        if raw_svc:
            self._service_name: str = raw_svc
            self._schema: Optional[str] = raw_db.upper() if raw_db else None
        elif raw_db.lower() in known_services:
            self._service_name = raw_db
            self._schema = None
        else:
            self._service_name = "FREEPDB1"
            self._schema = raw_db.upper() if raw_db else None
        self._sid: Optional[str] = opts.get("sid")
        self._user: str = opts.get("user", "system").strip()
        self._password: str = opts.get("password", "").strip()

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

    def _get_schema(self) -> Optional[str]:
        """Kembalikan schema/owner yang dipakai untuk query tabel."""
        return self._schema

