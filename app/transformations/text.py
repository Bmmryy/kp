"""Text Transformation Module for FlowETL.

Provides robust, modular string transformations including Trim, Capitalize (Title Case),
Uppercase, and Lowercase.
"""

from typing import List, Optional
from app.schema.models import DataType, Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry


class TrimTransformer(Transformer):
    """Trims whitespace from string columns in the dataset.

    Params:
        columns: Optional[List[str]] — Specific columns to trim. If omitted, trims all string columns.
    """

    def transform(self, dataset: Dataset) -> Dataset:
        target_cols = self.config.params.get("columns")
        string_cols = {
            col.name for col in dataset.schema_def.columns if col.data_type == DataType.STRING
        }
        cols_to_trim = set(target_cols) if target_cols else string_cols

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for col_name in cols_to_trim:
                val = new_row.get(col_name)
                if isinstance(val, str):
                    new_row[col_name] = val.strip()
            transformed_rows.append(new_row)

        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


class CapitalizeTransformer(Transformer):
    """Capitalizes string columns in the dataset.

    Params:
        columns: Optional[List[str]] — Specific columns to capitalize. If omitted, capitalizes all string columns.
        mode: str — 'title' (default, e.g. 'John Doe') or 'sentence' (e.g. 'John doe')
    """

    def transform(self, dataset: Dataset) -> Dataset:
        target_cols = self.config.params.get("columns")
        mode = self.config.params.get("mode", "title").lower()
        string_cols = {
            col.name for col in dataset.schema_def.columns if col.data_type == DataType.STRING
        }
        cols_to_cap = set(target_cols) if target_cols else string_cols

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for col_name in cols_to_cap:
                val = new_row.get(col_name)
                if isinstance(val, str):
                    if mode == "title":
                        new_row[col_name] = val.title()
                    else:
                        new_row[col_name] = val.capitalize()
            transformed_rows.append(new_row)

        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


class CaseTransformer(Transformer):
    """Converts string columns to UPPERCASE or lowercase.

    Params:
        mode: 'upper' | 'lower'
        columns: Optional[List[str]]
    """

    def transform(self, dataset: Dataset) -> Dataset:
        mode = self.config.params.get("mode", "upper").lower()
        target_cols = self.config.params.get("columns")
        string_cols = {
            col.name for col in dataset.schema_def.columns if col.data_type == DataType.STRING
        }
        cols_to_transform = set(target_cols) if target_cols else string_cols

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for col_name in cols_to_transform:
                val = new_row.get(col_name)
                if isinstance(val, str):
                    new_row[col_name] = val.upper() if mode == "upper" else val.lower()
            transformed_rows.append(new_row)

        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


# Register with TransformationRegistry
TransformationRegistry.register("trim", TrimTransformer)
TransformationRegistry.register("capitalize", CapitalizeTransformer)
TransformationRegistry.register("case", CaseTransformer)
# Convenience aliases — pre-fills mode param automatically
class _UpperCaseTransformer(CaseTransformer):
    def transform(self, dataset):
        self.config.params.setdefault("mode", "upper")
        return super().transform(dataset)

class _LowerCaseTransformer(CaseTransformer):
    def transform(self, dataset):
        self.config.params.setdefault("mode", "lower")
        return super().transform(dataset)

TransformationRegistry.register("uppercase", _UpperCaseTransformer)
TransformationRegistry.register("lowercase", _LowerCaseTransformer)
