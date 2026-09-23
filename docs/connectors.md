# FlowETL Connector Architecture

## 1. Connector Interface Contract

Connectors decouple specific external data stores (MySQL, PostgreSQL, SQLite, CSV, etc.) from the rest of the ETL pipeline.

All connectors must subclass either `SourceConnector` or `DestinationConnector` and register themselves with `ConnectorRegistry`.

### 1.1 Source Connector Contract

```python
class SourceConnector(ABC):
    def connect(self) -> None:
        """Establish connection to data source."""

    def test_connection(self) -> bool:
        """Test authentication and reachability."""

    def list_tables(self) -> List[str]:
        """Discover available tables or datasets."""

    def get_schema(self, table_name: str) -> TableSchema:
        """Discover source schema and translate into canonical TableSchema."""

    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        """Yield batches of canonical Datasets."""

    def close(self) -> None:
        """Safely release connections and resources."""
```

### 1.2 Destination Connector Contract

```python
class DestinationConnector(ABC):
    def connect(self) -> None:
        """Establish connection to target store."""

    def test_connection(self) -> bool:
        """Test write privileges and reachability."""

    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Translate canonical TableSchema to native DDL and execute."""

    def load(self, dataset: Dataset, table_name: str, mode: str = "append") -> int:
        """Insert or bulk-load canonical records into destination table."""

    def close(self) -> None:
        """Safely release connections and resources."""
```

---

## 2. Registering a Connector

New connectors are dynamically registered in `ConnectorRegistry`:

```python
from app.connectors.registry import ConnectorRegistry

# Registering a new source
ConnectorRegistry.register_source("custom_source", CustomSourceConnector)

# Registering a new destination
ConnectorRegistry.register_destination("custom_dest", CustomDestinationConnector)
```
