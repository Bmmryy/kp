"""Column Selection & Mapping Transformation Module for FlowETL.

Provides transformers for:
1. SelectColumnsTransformer: Selecting a subset of columns from the dataset.
2. ColumnMappingTransformer: Mapping source columns to destination target columns (renaming + projection).
3. AddColumnTransformer: Adding a new derived/constant column.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry


class SelectColumnsTransformer(Transformer):
    """Filters dataset to include only specified columns.

    Params:
        columns: List[str] — ordered list of column names to retain.
    """

    def transform(self, dataset: Dataset) -> Dataset:
        target_cols: List[str] = self.config.params.get("columns", [])
        if not target_cols:
            return dataset

        valid_col_names = {c.name for c in dataset.schema_def.columns}
        selected = [c for c in target_cols if c in valid_col_names]
        if not selected:
            return dataset

        new_columns = [
            dataset.schema_def.get_column(c)
            for c in selected
            if dataset.schema_def.get_column(c) is not None
        ]
        new_schema = TableSchema(
            name=dataset.schema_def.name,
            columns=new_columns,  # type: ignore
            metadata=dataset.schema_def.metadata.copy(),
        )

        selected_set = set(selected)
        transformed_rows = [
            {k: v for k, v in row.items() if k in selected_set}
            for row in dataset.rows
        ]

        return Dataset(schema=new_schema, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        target_cols = self.config.params.get("columns", [])
        if not target_cols:
            return input_schema
        new_cols = [c for c in input_schema.columns if c.name in target_cols]
        return TableSchema(name=input_schema.name, columns=new_cols, metadata=input_schema.metadata)


class ColumnMappingTransformer(Transformer):
    """Maps and renames source columns to target columns.

    Params:
        mapping: Dict[str, str] — { "source_col_name": "target_col_name" }
        drop_unmapped: bool — If True (default), drops source columns not present in mapping.
        target_table: Optional[str] — Optional target table name to update schema name.
    """

    def transform(self, dataset: Dataset) -> Dataset:
        mapping: Dict[str, str] = self.config.params.get("mapping", {})
        drop_unmapped: bool = self.config.params.get("drop_unmapped", True)
        target_table: Optional[str] = self.config.params.get("target_table")

        if not mapping:
            return dataset

        new_columns: List[ColumnDefinition] = []
        for col in dataset.schema_def.columns:
            if col.name in mapping:
                target_col_name = mapping[col.name]
                new_col = ColumnDefinition(
                    name=target_col_name,
                    data_type=col.data_type,
                    nullable=col.nullable,
                    primary_key=col.primary_key,
                    unique=col.unique,
                    default=col.default,
                    metadata=col.metadata.copy(),
                )
                new_columns.append(new_col)
            elif not drop_unmapped:
                new_columns.append(col.model_copy(deep=True))

        new_schema = TableSchema(
            name=target_table or dataset.schema_def.name,
            columns=new_columns,
            metadata=dataset.schema_def.metadata.copy(),
        )

        transformed_rows = []
        for row in dataset.rows:
            new_row: Dict[str, Any] = {}
            for src_name, val in row.items():
                if src_name in mapping:
                    target_name = mapping[src_name]
                    new_row[target_name] = val
                elif not drop_unmapped:
                    new_row[src_name] = val
            transformed_rows.append(new_row)

        return Dataset(schema=new_schema, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        mapping: Dict[str, str] = self.config.params.get("mapping", {})
        drop_unmapped: bool = self.config.params.get("drop_unmapped", True)
        target_table: Optional[str] = self.config.params.get("target_table")
        new_cols: List[ColumnDefinition] = []
        for col in input_schema.columns:
            if col.name in mapping:
                new_cols.append(col.model_copy(update={"name": mapping[col.name]}))
            elif not drop_unmapped:
                new_cols.append(col.model_copy(deep=True))
        return TableSchema(name=target_table or input_schema.name, columns=new_cols, metadata=input_schema.metadata)


class AddColumnTransformer(Transformer):
    """Adds a new column with a static default value to the dataset.

    Params:
        name: str — New column name.
        value: Any — Constant value for the column.
        data_type: str — Canonical data type string (default 'string').
    """

    def transform(self, dataset: Dataset) -> Dataset:
        col_name = self.config.params.get("name")
        if not col_name:
            return dataset

        col_val = self.config.params.get("value")
        type_str = self.config.params.get("data_type", "string")

        try:
            canonical_type = DataType.from_str(type_str)
        except Exception:
            canonical_type = DataType.STRING

        new_schema = dataset.schema_def.model_copy(deep=True)
        if not new_schema.has_column(col_name):
            new_schema.add_column(
                ColumnDefinition(
                    name=col_name,
                    data_type=canonical_type,
                    nullable=True,
                    default=col_val,
                )
            )

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            new_row[col_name] = col_val
            transformed_rows.append(new_row)

        return Dataset(schema=new_schema, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        col_name = self.config.params.get("name")
        if not col_name:
            return input_schema
        new_schema = input_schema.model_copy(deep=True)
        if not new_schema.has_column(col_name):
            new_schema.add_column(
                ColumnDefinition(
                    name=col_name,
                    data_type=DataType.STRING,
                    nullable=True,
                )
            )
        return new_schema


# Register with TransformationRegistry
TransformationRegistry.register("select_columns", SelectColumnsTransformer)
TransformationRegistry.register("column_mapping", ColumnMappingTransformer)
TransformationRegistry.register("add_column", AddColumnTransformer)
