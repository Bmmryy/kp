"""Connector Registry for FlowETL.

Maintains registry mappings of connector identifiers to concrete connector classes,
enabling dynamic discovery and runtime instantiation.
"""

from typing import Dict, Type
from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.exceptions import ConfigurationError


class ConnectorRegistry:
    """Registry for Source and Destination connector implementations."""

    _sources: Dict[str, Type[SourceConnector]] = {}
    _destinations: Dict[str, Type[DestinationConnector]] = {}

    @classmethod
    def register_source(cls, connector_type: str, connector_cls: Type[SourceConnector]) -> None:
        cls._sources[connector_type.lower()] = connector_cls

    @classmethod
    def register_destination(cls, connector_type: str, connector_cls: Type[DestinationConnector]) -> None:
        cls._destinations[connector_type.lower()] = connector_cls

    @classmethod
    def get_source_class(cls, connector_type: str) -> Type[SourceConnector]:
        key = connector_type.lower()
        if key not in cls._sources:
            raise ConfigurationError(
                f"Source connector '{connector_type}' is not registered.",
                suggested_action=f"Available source connectors: {list(cls._sources.keys())}",
            )
        return cls._sources[key]

    @classmethod
    def get_destination_class(cls, connector_type: str) -> Type[DestinationConnector]:
        key = connector_type.lower()
        if key not in cls._destinations:
            raise ConfigurationError(
                f"Destination connector '{connector_type}' is not registered.",
                suggested_action=f"Available destination connectors: {list(cls._destinations.keys())}",
            )
        return cls._destinations[key]

    @classmethod
    def create_source(cls, config: ConnectorConfig) -> SourceConnector:
        connector_cls = cls.get_source_class(config.connector_type)
        return connector_cls(config)

    @classmethod
    def create_destination(cls, config: ConnectorConfig) -> DestinationConnector:
        connector_cls = cls.get_destination_class(config.connector_type)
        return connector_cls(config)

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._sources.keys())

    @classmethod
    def list_destinations(cls) -> list[str]:
        return list(cls._destinations.keys())
