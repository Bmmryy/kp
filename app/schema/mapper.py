"""FlowETL Schema Mapping Engine.

Translates schemas and datasets between Source formats and Target formats,
applying column renaming, canonical type casting, column pruning,
and default value substitution.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.exceptions import SchemaMappingError
from app.schema.casting import cast_value, is_null_like
from app.schema.models import ColumnDefinition, Dataset, DataType, TableSchema


class ColumnMappingConfig(BaseModel):
    """Configuration mapping an individual source column to a target column."""

    source_column: str = Field(..., description="Name of column in source dataset")
    target_column: str = Field(..., description="Desired name in target dataset")
    target_type: Optional[DataType] = Field(None, description="Explicit canonical target type")
    nullable: Optional[bool] = Field(None, description="Override nullability in target")
    default_value: Optional[Any] = Field(None, description="Default value if null or missing")
    primary_key: Optional[bool] = Field(None, description="Override primary key constraint")


class SchemaMapper:
    """Engine that maps schemas and row records from source to destination definitions."""

    def __init__(
        self,
        target_table_name: str,
        column_mappings: Optional[List[ColumnMappingConfig]] = None,
        drop_unmapped: bool = True,
    ) -> None:
        self.target_table_name = target_table_name
        self.column_mappings = column_mappings or []
        self.drop_unmapped = drop_unmapped

    def map_schema(self, source_schema: TableSchema) -> TableSchema:
        """Generates the destination TableSchema based on mapping configurations."""
        target_columns: List[ColumnDefinition] = []

        if not self.column_mappings:
            # Identity mapping: 1-to-1 copy of source columns
            for col in source_schema.columns:
                target_columns.append(
                    ColumnDefinition(
                        name=col.name,
                        data_type=col.data_type,
                        nullable=col.nullable,
                        primary_key=col.primary_key,
                        unique=col.unique,
                        default=col.default,
                        metadata=dict(col.metadata),
                    )
                )
            return TableSchema(name=self.target_table_name, columns=target_columns)

        # Explicit mappings
        mapped_source_cols = set()
        for mapping in self.column_mappings:
            src_col = source_schema.get_column(mapping.source_column)
            if not src_col and mapping.default_value is None:
                raise SchemaMappingError(
                    message=f"Mapped source column '{mapping.source_column}' does not exist in schema '{source_schema.name}'.",
                    suggested_action=f"Select an existing source column from: {source_schema.column_names}",
                )

            mapped_source_cols.add(mapping.source_column)
            col_type = mapping.target_type or (src_col.data_type if src_col else DataType.STRING)
            col_nullable = (
                mapping.nullable if mapping.nullable is not None else (src_col.nullable if src_col else True)
            )
            col_pk = (
                mapping.primary_key if mapping.primary_key is not None else (src_col.primary_key if src_col else False)
            )

            target_columns.append(
                ColumnDefinition(
                    name=mapping.target_column,
                    data_type=col_type,
                    nullable=col_nullable,
                    primary_key=col_pk,
                    default=mapping.default_value,
                )
            )

        # Retain unmapped columns if drop_unmapped is False
        if not self.drop_unmapped:
            for col in source_schema.columns:
                if col.name not in mapped_source_cols:
                    target_columns.append(
                        ColumnDefinition(
                            name=col.name,
                            data_type=col.data_type,
                            nullable=col.nullable,
                            primary_key=col.primary_key,
                        )
                    )

        return TableSchema(name=self.target_table_name, columns=target_columns)

    def map_dataset(self, dataset: Dataset) -> Dataset:
        """Transforms records from source Dataset to conform to target mapped schema."""
        target_schema = self.map_schema(dataset.schema_def)
        transformed_rows: List[Dict[str, Any]] = []

        mapping_lookup: Dict[str, ColumnMappingConfig] = {
            m.source_column: m for m in self.column_mappings
        }

        for row in dataset.rows:
            new_row: Dict[str, Any] = {}
            if self.column_mappings:
                for mapping in self.column_mappings:
                    raw_val = row.get(mapping.source_column)
                    if is_null_like(raw_val) and mapping.default_value is not None:
                        raw_val = mapping.default_value

                    col_def = target_schema.get_column(mapping.target_column)
                    target_type = col_def.data_type if col_def else DataType.STRING
                    nullable = col_def.nullable if col_def else True

                    coerced_val = cast_value(
                        value=raw_val,
                        target_type=target_type,
                        column_name=mapping.target_column,
                        nullable=nullable,
                    )
                    new_row[mapping.target_column] = coerced_val

                if not self.drop_unmapped:
                    for k, v in row.items():
                        if k not in mapping_lookup:
                            new_row[k] = v
            else:
                # Identity mapping with type conformity
                for col in target_schema.columns:
                    raw_val = row.get(col.name)
                    if is_null_like(raw_val) and col.default is not None:
                        raw_val = col.default
                    coerced_val = cast_value(
                        value=raw_val,
                        target_type=col.data_type,
                        column_name=col.name,
                        nullable=col.nullable,
                    )
                    new_row[col.name] = coerced_val

            transformed_rows.append(new_row)

        return Dataset(schema=target_schema, rows=transformed_rows)
