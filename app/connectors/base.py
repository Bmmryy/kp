"""Base Connector Interfaces for FlowETL.

Defines the contract that all Source and Destination connectors must implement,
ensuring loose coupling and pluggability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional
from pydantic import BaseModel, Field

from app.schema.models import Dataset, TableSchema


class ConnectorConfig(BaseModel):
    """Base configuration model for all connectors."""

    name: str = Field(..., description="Unique name/alias for this connection")
    connector_type: str = Field(..., description="Connector identifier (e.g. mysql, postgresql, csv)")
    options: Dict[str, Any] = Field(default_factory=dict, description="Connector-specific parameters")


class SourceConnector(ABC):
    """Abstract Base Class for all Source Connectors in FlowETL."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection to the underlying data source."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verifies connection health and credentials. Returns True if valid."""
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """Discovers available tables, files, or collections in the source."""
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> TableSchema:
        """Extracts and converts source schema to FlowETL canonical TableSchema."""
        pass

    @abstractmethod
    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        """Extracts data as a stream/iterator of canonical Datasets."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Gracefully closes underlying connection resources."""
        pass

    def __enter__(self) -> "SourceConnector":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class DestinationConnector(ABC):
    """Abstract Base Class for all Destination Connectors in FlowETL."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection to the destination target."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verifies destination reachability and write privileges. Returns True if valid."""
        pass

    @abstractmethod
    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Creates table/collection in destination matching the canonical schema.

        Args:
            schema: Canonical TableSchema
            if_exists: Behavior if target exists ('fail', 'replace', 'append')
        """
        pass

    @abstractmethod
    def load(
        self,
        dataset: Dataset,
        table_name: str,
        mode: str = "append",
    ) -> int:
        """Loads canonical dataset rows into the destination target.

        Args:
            dataset: Canonical Dataset containing records
            table_name: Destination table or resource name
            mode: Write mode ('append', 'replace', 'truncate')

        Returns:
            int: Number of rows successfully written
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Gracefully closes destination connection resources."""
        pass

    def __enter__(self) -> "DestinationConnector":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
