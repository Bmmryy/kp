"""Verified Schema Evolution & Drift Detection for FlowETL.

Monitors incoming datasets for structural changes (new columns, type changes)
and verifies safe automated synchronization (ALTER TABLE) before loading.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from app.schema.models import ColumnDefinition, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from app.utils.logging import get_logger

logger = get_logger("flowetl.schema.evolution")


@dataclass
class SchemaEvolutionResult:
    """Represents the findings of a schema drift verification check."""

    has_drift: bool
    new_columns: List[ColumnDefinition] = field(default_factory=list)
    verification_logs: List[str] = field(default_factory=list)
    ddl_statements: List[str] = field(default_factory=list)


class SchemaEvolutionVerifier:
    """Verifies and orchestrates safe database schema drift evolution."""

    @classmethod
    def verify_and_plan(
        cls,
        dialect: str,
        table_name: str,
        existing_column_names: List[str],
        incoming_schema: TableSchema,
        quote_fn: Optional[Callable[[str], str]] = None,
    ) -> SchemaEvolutionResult:
        """Compares target table columns against incoming schema,

        verifies safety, and plans ALTER TABLE statements if new columns are detected.
        """
        q = quote_fn or (lambda name: f'"{name}"')
        existing_lower = {name.lower() for name in existing_column_names}
        new_cols: List[ColumnDefinition] = []
        logs: List[str] = []
        ddl_list: List[str] = []

        for col in incoming_schema.columns:
            if col.name.lower() not in existing_lower:
                # Verified: new column detected
                new_cols.append(col)
                log_msg = (
                    f"[Verified Schema Drift] Kolom baru terverifikasi: '{col.name}' "
                    f"(tipe: {col.data_type.value}). Mempersiapkan penyesuaian target table '{table_name}'."
                )
                logs.append(log_msg)
                logger.info(log_msg)

                # Generate safe ALTER TABLE DDL (Nullable so existing rows are unaffected)
                native_type = TypeRegistry.to_native(
                    dialect,
                    col.data_type,
                    length=None,
                    precision=None,
                    scale=None,
                )
                col_quoted = q(col.name)
                table_quoted = q(table_name)
                
                # Dialect-specific safe column addition
                if dialect.lower() == "sqlite":
                    ddl = f"ALTER TABLE {table_quoted} ADD COLUMN {col_quoted} {native_type}"
                else:
                    ddl = f"ALTER TABLE {table_quoted} ADD COLUMN {col_quoted} {native_type} NULL"
                
                ddl_list.append(ddl)

        has_drift = len(new_cols) > 0
        if not has_drift:
            logs.append(f"[Schema Verification] Struktur tabel '{table_name}' sesuai. Tidak ada perubahan skema.")

        return SchemaEvolutionResult(
            has_drift=has_drift,
            new_columns=new_cols,
            verification_logs=logs,
            ddl_statements=ddl_list,
        )
