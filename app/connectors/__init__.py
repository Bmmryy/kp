"""Connectors package for FlowETL with auto-registration of built-in drivers."""

from app.connectors.base import (
    ConnectorConfig,
    DestinationConnector,
    SourceConnector,
)
from app.connectors.csv import CSVDestination, CSVSource
from app.connectors.json import JSONDestination, JSONSource
from app.connectors.mysql import MySQLDestination, MySQLSource
from app.connectors.postgresql import PostgreSQLDestination, PostgreSQLSource
from app.connectors.registry import ConnectorRegistry
from app.connectors.sqlite import SQLiteDestination, SQLiteSource


def _register_builtin_connectors() -> None:
    # CSV
    ConnectorRegistry.register_source("csv", CSVSource)
    ConnectorRegistry.register_destination("csv", CSVDestination)

    # JSON & JSON Lines
    ConnectorRegistry.register_source("json", JSONSource)
    ConnectorRegistry.register_destination("json", JSONDestination)
    ConnectorRegistry.register_source("jsonl", JSONSource)
    ConnectorRegistry.register_destination("jsonl", JSONDestination)

    # SQLite
    ConnectorRegistry.register_source("sqlite", SQLiteSource)
    ConnectorRegistry.register_destination("sqlite", SQLiteDestination)

    # MySQL
    ConnectorRegistry.register_source("mysql", MySQLSource)
    ConnectorRegistry.register_destination("mysql", MySQLDestination)

    # PostgreSQL (both aliases)
    ConnectorRegistry.register_source("postgresql", PostgreSQLSource)
    ConnectorRegistry.register_destination("postgresql", PostgreSQLDestination)
    ConnectorRegistry.register_source("postgres", PostgreSQLSource)
    ConnectorRegistry.register_destination("postgres", PostgreSQLDestination)


# Trigger auto-registration
_register_builtin_connectors()

__all__ = [
    "ConnectorConfig",
    "SourceConnector",
    "DestinationConnector",
    "ConnectorRegistry",
    "CSVSource",
    "CSVDestination",
    "JSONSource",
    "JSONDestination",
    "SQLiteSource",
    "SQLiteDestination",
    "MySQLSource",
    "MySQLDestination",
    "PostgreSQLSource",
    "PostgreSQLDestination",
]
