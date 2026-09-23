"""FlowETL Universal Type Registry.

Enables bi-directional mapping between external database/file data types
and FlowETL's canonical DataType intermediate representation (IR):

    Source Dialect Native Type ──▶ Canonical DataType ──▶ Destination Dialect DDL
"""

import re
from typing import Callable, Dict, Optional, Tuple
from app.core.exceptions import SchemaMappingError
from app.schema.models import DataType


class TypeRegistry:
    """Registry maintaining native-to-canonical and canonical-to-native type mappings."""

    # {dialect: [(regex_pattern, Canonical DataType)]}
    _native_to_canonical: Dict[str, list[Tuple[re.Pattern, DataType]]] = {}

    # {dialect: {Canonical DataType: native_ddl_generator_or_str}}
    _canonical_to_native: Dict[str, Dict[DataType, str]] = {}

    @classmethod
    def register_native_mapping(
        cls,
        dialect: str,
        type_pattern: str,
        canonical_type: DataType,
    ) -> None:
        """Registers a regex pattern for mapping native types to canonical DataType."""
        d = dialect.lower()
        if d not in cls._native_to_canonical:
            cls._native_to_canonical[d] = []
        pattern = re.compile(type_pattern, re.IGNORECASE)
        cls._native_to_canonical[d].append((pattern, canonical_type))

    @classmethod
    def register_native_target(
        cls,
        dialect: str,
        canonical_type: DataType,
        native_type: str,
    ) -> None:
        """Registers the default native DDL type representation for a canonical type."""
        d = dialect.lower()
        if d not in cls._canonical_to_native:
            cls._canonical_to_native[d] = {}
        cls._canonical_to_native[d][canonical_type] = native_type

    @classmethod
    def to_canonical(cls, dialect: str, native_type: str) -> DataType:
        """Maps a dialect native type string to a canonical DataType."""
        d = dialect.lower()
        cleaned = native_type.strip()

        # Check registered patterns for the dialect
        patterns = cls._native_to_canonical.get(d, [])
        for pattern, canonical_type in patterns:
            if pattern.search(cleaned):
                return canonical_type

        # Fallback to general from_str if not matched by dialect
        # Extract base type name before parentheses e.g. VARCHAR(255) -> VARCHAR
        base_name = re.sub(r"\(.*?\)", "", cleaned).strip()
        try:
            return DataType.from_str(base_name)
        except ValueError:
            raise SchemaMappingError(
                message=f"Unsupported native type '{native_type}' for dialect '{dialect}'.",
                details=f"Dialect '{dialect}' has no matching canonical rule for '{native_type}'.",
                suggested_action=f"Register a custom type mapping for dialect '{dialect}' in TypeRegistry.",
            )

    @classmethod
    def to_native(
        cls,
        dialect: str,
        canonical_type: DataType,
        length: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
    ) -> str:
        """Translates a canonical DataType into the native target DDL string."""
        d = dialect.lower()
        dialect_map = cls._canonical_to_native.get(d)
        if not dialect_map or canonical_type not in dialect_map:
            raise SchemaMappingError(
                message=f"Dialect '{dialect}' has no target mapping for canonical type '{canonical_type.value}'.",
                suggested_action=f"Define DDL translation for '{canonical_type.value}' in dialect '{dialect}'.",
            )

        base_native = dialect_map[canonical_type]

        # Dynamic dimension adjustments if requested
        if canonical_type == DataType.STRING and length:
            if "varchar" in base_native.lower():
                return f"VARCHAR({length})"
        elif canonical_type == DataType.DECIMAL and precision and scale:
            if "decimal" in base_native.lower() or "numeric" in base_native.lower():
                return f"DECIMAL({precision}, {scale})"

        return base_native


def _initialize_default_type_mappings() -> None:
    """Pre-populates default type mappings for standard supported databases."""

    # ==========================================
    # PostgreSQL Mappings
    # ==========================================
    pg_mappings = [
        (r"^(smallint|int2|int4|integer|int|bigint|int8|serial|bigserial)", DataType.INTEGER),
        (r"^(boolean|bool)", DataType.BOOLEAN),
        (r"^(real|float4|float8|double precision|float)", DataType.FLOAT),
        (r"^(numeric|decimal)", DataType.DECIMAL),
        (r"^(character varying|varchar|character|char|text|citext)", DataType.STRING),
        (r"^date", DataType.DATE),
        (r"^(timestamp|timestamptz)", DataType.DATETIME),
        (r"^(time|timetz)", DataType.TIME),
        (r"^(json|jsonb)", DataType.JSON),
        (r"^(bytea|blob)", DataType.BINARY),
    ]
    for pat, c_type in pg_mappings:
        TypeRegistry.register_native_mapping("postgresql", pat, c_type)
        TypeRegistry.register_native_mapping("postgres", pat, c_type)

    pg_targets = {
        DataType.INTEGER: "INTEGER",
        DataType.FLOAT: "DOUBLE PRECISION",
        DataType.DECIMAL: "NUMERIC(18, 4)",
        DataType.STRING: "VARCHAR(255)",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMP",
        DataType.TIME: "TIME",
        DataType.JSON: "JSONB",
        DataType.BINARY: "BYTEA",
    }
    for c_type, native in pg_targets.items():
        TypeRegistry.register_native_target("postgresql", c_type, native)
        TypeRegistry.register_native_target("postgres", c_type, native)

    # ==========================================
    # MySQL Mappings
    # ==========================================
    mysql_mappings = [
        (r"^tinyint\(1\)", DataType.BOOLEAN),
        (r"^(tinyint|smallint|mediumint|int|integer|bigint)", DataType.INTEGER),
        (r"^(bool|boolean)", DataType.BOOLEAN),
        (r"^(float|double|real)", DataType.FLOAT),
        (r"^(decimal|numeric)", DataType.DECIMAL),
        (r"^(char|varchar|tinytext|text|mediumtext|longtext|enum|set)", DataType.STRING),
        (r"^date$", DataType.DATE),
        (r"^(datetime|timestamp)", DataType.DATETIME),
        (r"^time$", DataType.TIME),
        (r"^json$", DataType.JSON),
        (r"^(blob|tinyblob|mediumblob|longblob|binary|varbinary)", DataType.BINARY),
    ]
    for pat, c_type in mysql_mappings:
        TypeRegistry.register_native_mapping("mysql", pat, c_type)

    mysql_targets = {
        DataType.INTEGER: "INT",
        DataType.FLOAT: "DOUBLE",
        DataType.DECIMAL: "DECIMAL(18, 4)",
        DataType.STRING: "VARCHAR(255)",
        DataType.BOOLEAN: "TINYINT(1)",
        DataType.DATE: "DATE",
        DataType.DATETIME: "DATETIME",
        DataType.TIME: "TIME",
        DataType.JSON: "JSON",
        DataType.BINARY: "BLOB",
    }
    for c_type, native in mysql_targets.items():
        TypeRegistry.register_native_target("mysql", c_type, native)

    # ==========================================
    # SQLite Mappings
    # ==========================================
    sqlite_mappings = [
        (r"^(int|integer|tinyint|smallint|mediumint|bigint)", DataType.INTEGER),
        (r"^(real|double|float)", DataType.FLOAT),
        (r"^(numeric|decimal)", DataType.DECIMAL),
        (r"^(text|char|varchar|clob)", DataType.STRING),
        (r"^bool", DataType.BOOLEAN),
        (r"^(datetime|timestamp)", DataType.DATETIME),
        (r"^date", DataType.DATE),
        (r"^blob", DataType.BINARY),
    ]
    for pat, c_type in sqlite_mappings:
        TypeRegistry.register_native_mapping("sqlite", pat, c_type)

    sqlite_targets = {
        DataType.INTEGER: "INTEGER",
        DataType.FLOAT: "REAL",
        DataType.DECIMAL: "NUMERIC",
        DataType.STRING: "TEXT",
        DataType.BOOLEAN: "INTEGER",
        DataType.DATE: "TEXT",
        DataType.DATETIME: "TEXT",
        DataType.TIME: "TEXT",
        DataType.JSON: "TEXT",
        DataType.BINARY: "BLOB",
    }
    for c_type, native in sqlite_targets.items():
        TypeRegistry.register_native_target("sqlite", c_type, native)

    # ==========================================
    # SQL Server (MSSQL) Mappings
    # ==========================================
    mssql_mappings = [
        (r"^bit$", DataType.BOOLEAN),
        (r"^(tinyint|smallint|int|bigint)", DataType.INTEGER),
        (r"^(float|real)", DataType.FLOAT),
        (r"^(decimal|numeric|money|smallmoney)", DataType.DECIMAL),
        (r"^(char|varchar|text|nchar|nvarchar|ntext)", DataType.STRING),
        (r"^date$", DataType.DATE),
        (r"^(datetime|datetime2|smalldatetime)", DataType.DATETIME),
        (r"^time$", DataType.TIME),
        (r"^(binary|varbinary|image)", DataType.BINARY),
    ]
    for pat, c_type in mssql_mappings:
        TypeRegistry.register_native_mapping("sqlserver", pat, c_type)
        TypeRegistry.register_native_mapping("mssql", pat, c_type)

    mssql_targets = {
        DataType.INTEGER: "INT",
        DataType.FLOAT: "FLOAT",
        DataType.DECIMAL: "DECIMAL(18, 4)",
        DataType.STRING: "NVARCHAR(255)",
        DataType.BOOLEAN: "BIT",
        DataType.DATE: "DATE",
        DataType.DATETIME: "DATETIME2",
        DataType.TIME: "TIME",
        DataType.JSON: "NVARCHAR(MAX)",
        DataType.BINARY: "VARBINARY(MAX)",
    }
    for c_type, native in mssql_targets.items():
        TypeRegistry.register_native_target("sqlserver", c_type, native)
        TypeRegistry.register_native_target("mssql", c_type, native)

    # ==========================================
    # CSV / Flat File Mappings
    # ==========================================
    file_mappings = [
        (r"^(int|integer)$", DataType.INTEGER),
        (r"^(float|double|number)$", DataType.FLOAT),
        (r"^(decimal|numeric)$", DataType.DECIMAL),
        (r"^(str|string|text|varchar)$", DataType.STRING),
        (r"^(bool|boolean)$", DataType.BOOLEAN),
        (r"^date$", DataType.DATE),
        (r"^(datetime|timestamp)$", DataType.DATETIME),
        (r"^json$", DataType.JSON),
    ]
    for pat, c_type in file_mappings:
        TypeRegistry.register_native_mapping("csv", pat, c_type)
        TypeRegistry.register_native_mapping("json", pat, c_type)
        TypeRegistry.register_native_mapping("excel", pat, c_type)

    file_targets = {
        DataType.INTEGER: "integer",
        DataType.FLOAT: "float",
        DataType.DECIMAL: "decimal",
        DataType.STRING: "string",
        DataType.BOOLEAN: "boolean",
        DataType.DATE: "date",
        DataType.DATETIME: "datetime",
        DataType.TIME: "time",
        DataType.JSON: "json",
        DataType.BINARY: "string",
    }
    for c_type, native in file_targets.items():
        TypeRegistry.register_native_target("csv", c_type, native)
        TypeRegistry.register_native_target("json", c_type, native)
        TypeRegistry.register_native_target("excel", c_type, native)


# Auto-initialize standard mappings on module load
_initialize_default_type_mappings()
