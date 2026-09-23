"""FlowETL JSON & JSON Lines (NDJSON) Source and Destination Connectors.

Supports extracting and loading standard JSON arrays and line-delimited JSON (jsonl).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from app.connectors.base import ConnectorConfig, DestinationConnector, SourceConnector
from app.core.exceptions import (
    ConnectionFailedError,
    ExtractionError,
    LoadError,
    SchemaDiscoveryError,
)
from app.schema.models import Dataset, TableSchema
from app.utils.logging import get_logger

logger = get_logger("flowetl.connectors.json")


class JSONSource(SourceConnector):
    """Source connector for ingesting JSON and JSON Lines files."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.base_path = Path(config.options.get("path", "."))
        self.encoding = config.options.get("encoding", "utf-8")
        self.is_lines = config.options.get("lines", False)

    def _resolve_file_path(self, table_name: str) -> Path:
        if self.base_path.suffix or (self.base_path.exists() and self.base_path.is_file()):
            return self.base_path
        file_path = self.base_path / table_name
        if not file_path.suffix:
            file_path = file_path.with_suffix(".jsonl" if self.is_lines else ".json")
        return file_path

    def connect(self) -> None:
        if not self.base_path.exists():
            raise ConnectionFailedError(
                message=f"JSON source path does not exist: {self.base_path.resolve()}",
                suggested_action="Verify the 'path' parameter in your JSON connection configuration.",
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
        exts = ["*.json", "*.jsonl", "*.ndjson"]
        files = []
        for ext in exts:
            files.extend([f.stem for f in self.base_path.glob(ext)])
        return sorted(list(set(files)))

    def _read_sample_records(self, file_path: Path, limit: int = 100) -> List[Dict[str, Any]]:
        samples: List[Dict[str, Any]] = []
        with open(file_path, "r", encoding=self.encoding) as f:
            if self.is_lines or file_path.suffix in (".jsonl", ".ndjson"):
                for line in f:
                    if line.strip():
                        samples.append(json.loads(line))
                        if len(samples) >= limit:
                            break
            else:
                data = json.load(f)
                if isinstance(data, list):
                    samples = data[:limit]
                elif isinstance(data, dict):
                    samples = [data]
        return samples

    def get_schema(self, table_name: str) -> TableSchema:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(table_name)
        if not file_path.exists():
            raise SchemaDiscoveryError(
                message=f"JSON file not found for table '{table_name}' at {file_path.resolve()}.",
                suggested_action="Ensure the specified file exists in the directory.",
            )

        try:
            sample_records = self._read_sample_records(file_path, limit=100)
            dataset = Dataset.infer_from_dicts(name=table_name, rows=sample_records)
            return dataset.schema_def
        except Exception as err:
            raise SchemaDiscoveryError(
                message=f"Failed to infer schema from JSON '{file_path}': {err}",
                details=str(err),
            ) from err

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
                message=f"Cannot extract from missing JSON file: {file_path.resolve()}",
            )

        schema = self.get_schema(table_name)
        effective_chunk_size = chunk_size or 5000

        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                if self.is_lines or file_path.suffix in (".jsonl", ".ndjson"):
                    batch: List[Dict[str, Any]] = []
                    for line in f:
                        if line.strip():
                            batch.append(json.loads(line))
                            if len(batch) >= effective_chunk_size:
                                yield Dataset(schema=schema, rows=batch)
                                batch = []
                    if batch:
                        yield Dataset(schema=schema, rows=batch)
                else:
                    data = json.load(f)
                    records = data if isinstance(data, list) else [data]
                    for i in range(0, len(records), effective_chunk_size):
                        yield Dataset(schema=schema, rows=records[i : i + effective_chunk_size])
        except Exception as err:
            raise ExtractionError(
                message=f"Error reading JSON records from '{file_path}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        self._is_connected = False


class JSONDestination(DestinationConnector):
    """Destination connector for writing datasets into JSON or JSON Lines files."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.base_path = Path(config.options.get("path", "."))
        self.encoding = config.options.get("encoding", "utf-8")
        self.is_lines = config.options.get("lines", False)
        self.indent = config.options.get("indent", 2 if not self.is_lines else None)

    def _resolve_file_path(self, table_name: str) -> Path:
        if self.base_path.suffix or (self.base_path.exists() and self.base_path.is_file()):
            return self.base_path
        target = self.base_path / table_name
        if not target.suffix:
            target = target.with_suffix(".jsonl" if self.is_lines else ".json")
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
                message=f"JSON destination file '{file_path.name}' already exists.",
                suggested_action="Set load mode to 'replace' or 'append'.",
            )
        if not file_path.exists() or if_exists == "replace":
            with open(file_path, "w", encoding=self.encoding) as f:
                if self.is_lines or file_path.suffix in (".jsonl", ".ndjson"):
                    pass  # Ready for lines
                else:
                    json.dump([], f)

    def load(
        self,
        dataset: Dataset,
        table_name: str,
        mode: str = "append",
    ) -> int:
        if not self.is_connected:
            self.connect()
        file_path = self._resolve_file_path(table_name)

        try:
            if self.is_lines or file_path.suffix in (".jsonl", ".ndjson"):
                write_mode = "w" if mode == "replace" or not file_path.exists() else "a"
                with open(file_path, write_mode, encoding=self.encoding) as f:
                    for row in dataset.rows:
                        f.write(json.dumps(row, default=str) + "\n")
            else:
                existing = []
                if file_path.exists() and mode == "append":
                    with open(file_path, "r", encoding=self.encoding) as f:
                        try:
                            content = json.load(f)
                            if isinstance(content, list):
                                existing = content
                        except json.JSONDecodeError:
                            existing = []
                combined = existing + dataset.rows if mode == "append" else dataset.rows
                with open(file_path, "w", encoding=self.encoding) as f:
                    json.dump(combined, f, indent=self.indent, default=str)

            return dataset.row_count
        except Exception as err:
            raise LoadError(
                message=f"Failed to load records into JSON '{file_path}': {err}",
                details=str(err),
            ) from err

    def close(self) -> None:
        self._is_connected = False
