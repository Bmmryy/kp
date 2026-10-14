"""Verified Schema Evolution & Drift Detection for FlowETL.

Monitors incoming datasets for structural changes (new columns, type changes)
and verifies safe automated synchronization (ALTER TABLE) before loading.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from app.schema.models import ColumnDefinition, DataType, TableSchema
from app.schema.type_registry import TypeRegistry
from app.utils.logging import get_logger

logger = get_logger("flowetl.schema.evolution")


@dataclass
class SchemaEvolutionResult:
    """Represents the findings of a schema drift verification check."""

    has_drift: bool
    new_columns: List[ColumnDefinition] = field(default_factory=list)
    modified_columns: List[ColumnDefinition] = field(default_factory=list)
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
        existing_columns_info: Optional[List[Dict[str, Any]]] = None,
    ) -> SchemaEvolutionResult:
        """Compares target table columns against incoming schema,

        verifies safety, and plans ALTER TABLE statements if new columns or type changes are detected.
        """
        q = quote_fn or (lambda name: f'"{name}"')
        existing_lower = {name.lower() for name in existing_column_names}
        existing_info_map = {
            c["name"].lower(): c for c in (existing_columns_info or []) if "name" in c
        }

        new_cols: List[ColumnDefinition] = []
        mod_cols: List[ColumnDefinition] = []
        logs: List[str] = []
        ddl_list: List[str] = []

        table_quoted = q(table_name)

        for col in incoming_schema.columns:
            col_name_lower = col.name.lower()
            col_quoted = q(col.name)
            # Check if column has metadata dimension overrides
            import re
            col_len = col.metadata.get("length") if col.metadata else None
            if col_len is None and col.metadata and "raw_type" in col.metadata:
                m_raw = re.search(r"\((\d+)\)", str(col.metadata["raw_type"]))
                if m_raw:
                    col_len = int(m_raw.group(1))
            col_prec = col.metadata.get("precision") if col.metadata else None
            col_scale = col.metadata.get("scale") if col.metadata else None

            native_type = TypeRegistry.to_native(
                dialect,
                col.data_type,
                length=col_len,
                precision=col_prec,
                scale=col_scale,
            )

            if col_name_lower not in existing_lower:
                # 1. New column detected -> ADD COLUMN
                new_cols.append(col)
                log_msg = (
                    f"[Verified Schema Drift] Kolom baru terverifikasi: '{col.name}' "
                    f"(tipe: {col.data_type.value}). Mempersiapkan penyesuaian target table '{table_name}'."
                )
                logs.append(log_msg)
                logger.info(log_msg)

                if dialect.lower() == "sqlite":
                    ddl = f"ALTER TABLE {table_quoted} ADD COLUMN {col_quoted} {native_type}"
                else:
                    ddl = f"ALTER TABLE {table_quoted} ADD COLUMN {col_quoted} {native_type} NULL"

                ddl_list.append(ddl)
            else:
                # 2. Existing column -> Check for type change (if inspector info available)
                if col_name_lower in existing_info_map:
                    exist_col = existing_info_map[col_name_lower]
                    exist_type_obj = exist_col.get("type")
                    exist_type_str = str(exist_type_obj).upper() if exist_type_obj else ""

                    # Check if target column needs alteration (canonical type or dimension drift)
                    target_canonical = TypeRegistry.to_canonical(dialect, exist_type_str)
                    needs_alteration = False

                    if target_canonical != col.data_type:
                        needs_alteration = True
                    elif dialect.lower() in ("mysql", "postgresql", "postgres"):
                        # Check length / precision widening
                        # e.g. VARCHAR(50) vs incoming VARCHAR(255) or VARCHAR vs TEXT
                        m_exist = re.search(r"\((\d+)(?:,\s*(\d+))?\)", exist_type_str)
                        m_incoming = re.search(r"\((\d+)(?:,\s*(\d+))?\)", native_type)
                        if m_exist and m_incoming:
                            exist_len = int(m_exist.group(1))
                            inc_len = int(m_incoming.group(1))
                            if inc_len > exist_len:
                                needs_alteration = True
                        elif m_exist and ("TEXT" in native_type.upper() or "LONGTEXT" in native_type.upper()):
                            needs_alteration = True
                        elif "TEXT" in exist_type_str.upper() and m_incoming:
                            pass

                    if needs_alteration and dialect.lower() in ("mysql", "postgresql", "postgres"):
                        mod_cols.append(col)
                        mod_msg = (
                            f"[Verified Schema Evolution] Perubahan tipe/kapasitas data terdeteksi pada '{col.name}': "
                            f"{exist_type_str} ──► {native_type}. Menyesuaikan tabel '{table_name}'."
                        )
                        logs.append(mod_msg)
                        logger.info(mod_msg)

                        if dialect.lower() == "mysql":
                            ddl = f"ALTER TABLE {table_quoted} MODIFY COLUMN {col_quoted} {native_type}"
                        else:
                            ddl = f"ALTER TABLE {table_quoted} ALTER COLUMN {col_quoted} TYPE {native_type}"

                        ddl_list.append(ddl)

        has_drift = (len(new_cols) > 0) or (len(mod_cols) > 0)
        if not has_drift:
            logs.append(f"[Schema Verification] Struktur tabel '{table_name}' sesuai. Tidak ada perubahan skema.")

        return SchemaEvolutionResult(
            has_drift=has_drift,
            new_columns=new_cols,
            modified_columns=mod_cols,
            verification_logs=logs,
            ddl_statements=ddl_list,
        )
