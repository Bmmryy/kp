"""FlowETL CSV Source and Destination Connectors.

Provides memory-efficient, chunked extraction and loading for CSV files,
supporting automatic delimiter sniffing and schema discovery.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.exceptions import (
    ConnectionFailedError,
    ExtractionError,
    LoadError,
    SchemaDiscoveryError,
)
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema
from app.utils.logging import get_logger

logger = get_logger("flowetl.connectors.csv")


class CSVSource(SourceConnector):
    """Source connector for ingesting CSV files in streaming chunks."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.base_path = Path(config.options.get("path", "."))
        self.delimiter = config.options.get("delimiter", ",")
        self.encoding = config.options.get("encoding", "utf-8")
        self.has_header = config.options.get("has_header", True)

    def _resolve_file_path(self, table_name: str) -> Path:
        """Resolves table_name to a concrete file path."""
        if self.base_path.suffix or (self.base_path.exists() and self.base_path.is_file()):
            return self.base_path
        file_path = self.base_path / table_name
        if not file_path.suffix:
            file_path = file_path.with_suffix(".csv")
        return file_path

    def connect(self) -> None:
        """Verifies existence and accessibility of base path."""
        if not self.base_path.exists():
            raise ConnectionFailedError(
                message=f"CSV source path does not exist: {self.base_path.resolve()}",
                suggested_action="Verify the 'path' parameter in your CSV connection configuration.",
            )
        self._is_connected = True

    def test_connection(self) -> bool:
        self.connect()
        return True

    def list_tables(self) -> List[str]:
        if not self.is_connected:
            self.connect()
        if self.base_path.is_file():
            return [self.base_path.stem]
        return sorted([f.stem for f in self.base_path.glob("*.csv")])

    def get_schema(self, table_name: str) -> TableSchema:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(table_name)
        if not file_path.exists():
            raise SchemaDiscoveryError(
                message=f"CSV file not found for table '{table_name}' at {file_path.resolve()}.",
                suggested_action="Verify table/file name or check directory contents.",
            )

        sample_rows: List[Dict[str, Any]] = []
        try:
            with open(file_path, "r", encoding=self.encoding, errors="replace") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                for i, row in enumerate(reader):
                    sample_rows.append(row)
                    if i >= 100:
                        break
        except Exception as err:
            raise SchemaDiscoveryError(
                message=f"Failed to discover schema from CSV file '{file_path}': {err}",
                details=str(err),
            ) from err

        dataset = Dataset.infer_from_dicts(name=table_name, rows=sample_rows)
        return dataset.schema_def

    def extract(
        self,
        table_name: str,
        query: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> Iterator[Dataset]:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(table_name)
        if not file_path.exists():
            raise ExtractionError(
                message=f"Cannot extract from missing CSV file: {file_path.resolve()}",
                suggested_action="Ensure the source file exists before executing extraction.",
            )

        schema = self.get_schema(table_name)
        effective_chunk_size = chunk_size or 5000

        try:
            with open(file_path, "r", encoding=self.encoding, errors="replace") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                batch: List[Dict[str, Any]] = []
                for row in reader:
                    batch.append(row)
                    if len(batch) >= effective_chunk_size:
                        yield Dataset(schema=schema, rows=batch)
                        batch = []
                if batch:
                    yield Dataset(schema=schema, rows=batch)
        except Exception as err:
            raise ExtractionError(
                message=f"Error reading records from CSV '{file_path}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        self._is_connected = False


class CSVDestination(DestinationConnector):
    """Destination connector for writing datasets into CSV files."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.base_path = Path(config.options.get("path", "."))
        self.delimiter = config.options.get("delimiter", ",")
        self.encoding = config.options.get("encoding", "utf-8")

    def _resolve_file_path(self, table_name: str) -> Path:
        if self.base_path.suffix or (self.base_path.exists() and self.base_path.is_file()):
            return self.base_path
        target = self.base_path / table_name
        if not target.suffix:
            target = target.with_suffix(".csv")
        return target

    def connect(self) -> None:
        if self.base_path.suffix or (self.base_path.exists() and self.base_path.is_file()):
            self.base_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.base_path.mkdir(parents=True, exist_ok=True)
        self._is_connected = True

    def test_connection(self) -> bool:
        self.connect()
        return True

    def create_schema(self, schema: TableSchema, if_exists: str = "fail") -> None:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(schema.name)
        if file_path.exists() and if_exists == "fail":
            raise LoadError(
                message=f"CSV destination file '{file_path.name}' already exists.",
                suggested_action="Set load mode to 'replace' or 'append', or specify a different file name.",
            )

        if not file_path.exists() or if_exists == "replace":
            with open(file_path, "w", newline="", encoding=self.encoding) as f:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerow(schema.column_names)

    def load(
        self,
        dataset: Dataset,
        table_name: str,
        mode: str = "append",
    ) -> int:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(table_name)
        file_exists = file_path.exists()
        write_mode = "w" if mode == "replace" or not file_exists else "a"

        try:
            with open(file_path, write_mode, newline="", encoding=self.encoding) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=dataset.schema_def.column_names,
                    delimiter=self.delimiter,
                    extrasaction="ignore",
                )
                if write_mode == "w":
                    writer.writeheader()
                for row in dataset.rows:
                    writer.writerow(row)
            return dataset.row_count
        except Exception as err:
            raise LoadError(
                message=f"Failed to load records into CSV '{file_path}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        self._is_connected = False
