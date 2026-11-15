"""FlowETL Internal Data Model & Canonical Type System.

Defines the universal intermediate representation (IR) for datasets,
table schemas, and column definitions that all connectors and transformers
interact with.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DataType(str, Enum):
    """Canonical data types supported across all FlowETL connectors."""

    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    JSON = "json"
    BINARY = "binary"

    @classmethod
    def from_str(cls, value: str) -> DataType:
        """Parses a string into a canonical DataType enum safely."""
        cleaned = value.strip().lower()
        mapping = {
            "int": cls.INTEGER,
            "integer": cls.INTEGER,
            "bigint": cls.INTEGER,
            "smallint": cls.INTEGER,
            "tinyint": cls.INTEGER,
            "float": cls.FLOAT,
            "double": cls.FLOAT,
            "real": cls.FLOAT,
            "decimal": cls.DECIMAL,
            "numeric": cls.DECIMAL,
            "str": cls.STRING,
            "string": cls.STRING,
            "varchar": cls.STRING,
            "char": cls.STRING,
            "text": cls.STRING,
            "bool": cls.BOOLEAN,
            "boolean": cls.BOOLEAN,
            "date": cls.DATE,
            "datetime": cls.DATETIME,
            "timestamp": cls.DATETIME,
            "time": cls.TIME,
            "json": cls.JSON,
            "jsonb": cls.JSON,
            "bytes": cls.BINARY,
            "binary": cls.BINARY,
            "blob": cls.BINARY,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown data type: '{value}'")


class ColumnDefinition(BaseModel):
    """Canonical definition of a dataset column."""

    model_config = ConfigDict(frozen=False)

    name: str = Field(..., description="Column name")
    data_type: DataType = Field(..., description="Canonical data type")
    nullable: bool = Field(True, description="Whether the column accepts null values")
    primary_key: bool = Field(False, description="Whether this column is a primary key")
    unique: bool = Field(False, description="Whether column values must be unique")
    default: Optional[Any] = Field(None, description="Default value if omitted")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Connector-specific or source metadata"
    )

    def is_compatible_value(self, val: Any) -> bool:
        """Quick check if a Python value is fundamentally compatible."""
        if val is None:
            return self.nullable
        if self.data_type == DataType.INTEGER and isinstance(val, int) and not isinstance(val, bool):
            return True
        if self.data_type == DataType.FLOAT and isinstance(val, (float, int)) and not isinstance(val, bool):
            return True
        if self.data_type == DataType.STRING and isinstance(val, str):
            return True
        if self.data_type == DataType.BOOLEAN and isinstance(val, bool):
            return True
        if self.data_type == DataType.DATETIME and isinstance(val, (datetime, str)):
            return True
        if self.data_type == DataType.DATE and isinstance(val, (date, str)):
            return True
        if self.data_type == DataType.DECIMAL and isinstance(val, (Decimal, float, int)):
            return True
        if self.data_type == DataType.JSON and isinstance(val, (dict, list)):
            return True
        return True


class TableSchema(BaseModel):
    """Universal schema representing table structure, types, and constraints."""

    name: str = Field(..., description="Table or dataset identifier")
    columns: List[ColumnDefinition] = Field(
        default_factory=list, description="Ordered list of column definitions"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Table-level metadata (engine, charset, etc.)"
    )

    @property
    def column_names(self) -> List[str]:
        return [c.name for c in self.columns]

    @property
    def primary_keys(self) -> List[str]:
        return [c.name for c in self.columns if c.primary_key]

    def get_column(self, col_name: str) -> Optional[ColumnDefinition]:
        for col in self.columns:
            if col.name == col_name:
                return col
        return None

    def has_column(self, col_name: str) -> bool:
        return self.get_column(col_name) is not None

    def add_column(self, col: ColumnDefinition) -> None:
        if self.has_column(col.name):
            raise ValueError(f"Column '{col.name}' already exists in schema '{self.name}'.")
        self.columns.append(col)

    def drop_column(self, col_name: str) -> None:
        self.columns = [c for c in self.columns if c.name != col_name]

    def rename_column(self, old_name: str, new_name: str) -> None:
        col = self.get_column(old_name)
        if not col:
            raise ValueError(f"Column '{old_name}' not found in schema '{self.name}'.")
        if self.has_column(new_name) and old_name != new_name:
            raise ValueError(f"Column '{new_name}' already exists in schema '{self.name}'.")
        col.name = new_name


class Dataset(BaseModel):
    """Canonical dataset containing tabular rows and its associated TableSchema."""

    schema_def: TableSchema = Field(..., alias="schema", description="Schema metadata")
    rows: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tabular records (list of row dicts)"
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.schema_def.columns)

    def head(self, n: int = 5) -> Dataset:
        """Returns a new Dataset containing up to n sample rows."""
        return Dataset(schema=self.schema_def, rows=self.rows[:n])

    @classmethod
    def infer_from_dicts(cls, name: str, rows: List[Dict[str, Any]]) -> Dataset:
        """Infers a canonical TableSchema and constructs a Dataset from dictionary rows."""
        if not rows:
            return cls(schema=TableSchema(name=name, columns=[]), rows=[])

        import re

        def _detect_type(v: Any) -> Optional[DataType]:
            if v is None:
                return None
            if isinstance(v, Decimal):
                return DataType.DECIMAL
            if isinstance(v, bool):
                return DataType.BOOLEAN
            if isinstance(v, int):
                return DataType.INTEGER
            if isinstance(v, float):
                return DataType.FLOAT
            if isinstance(v, datetime):
                return DataType.DATETIME
            if isinstance(v, date):
                return DataType.DATE
            if isinstance(v, (dict, list)):
                return DataType.JSON
            if isinstance(v, str):
                s = v.strip()
                if not s or s.lower() in ("null", "none", "nan"):
                    return None
                if s.lower() in ("true", "false"):
                    return DataType.BOOLEAN
                if re.match(r"^-?\d+\.\d{3,}$", s):
                    return DataType.DECIMAL
                if re.match(r"^-?\d+\.\d+$", s):
                    return DataType.FLOAT
                if re.match(r"^-?\d+$", s):
                    return DataType.INTEGER
                if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                    return DataType.DATE
                if re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", s):
                    return DataType.DATETIME
                return DataType.STRING
            return DataType.STRING

        def _widen_type(curr: DataType, new_t: DataType) -> DataType:
            if curr == new_t:
                return curr
            if curr == DataType.STRING or new_t == DataType.STRING:
                return DataType.STRING
            types = {curr, new_t}
            if types <= {DataType.INTEGER, DataType.FLOAT}:
                return DataType.FLOAT
            if types <= {DataType.INTEGER, DataType.DECIMAL}:
                return DataType.DECIMAL
            if types <= {DataType.FLOAT, DataType.DECIMAL}:
                return DataType.DECIMAL
            if types <= {DataType.DATE, DataType.DATETIME}:
                return DataType.DATETIME
            return DataType.STRING

        all_keys: Dict[str, DataType] = {}
        for r in rows[:100]:  # inspect up to 100 rows
            for k, v in r.items():
                inferred = _detect_type(v)
                if inferred is None:
                    continue
                if k not in all_keys:
                    all_keys[k] = inferred
                else:
                    all_keys[k] = _widen_type(all_keys[k], inferred)

        cols = [
            ColumnDefinition(
                name=k,
                data_type=all_keys.get(k, DataType.STRING),
                nullable=True,
                primary_key=(k.lower() in ("id", f"{name.lower()}_id")),
            )
            for k in all_keys.keys()
        ]
        return cls(schema=TableSchema(name=name, columns=cols), rows=rows)
