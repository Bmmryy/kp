"""Data Cleansing Module for FlowETL.

Provides FillNull, DropNull, and Data Masking transformers.
"""

from typing import Any, Dict, List, Optional
from app.schema.models import Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry


class FillNullTransformer(Transformer):
    """Fills null / None values in rows with a default replacement value.

    Params:
        default_value: Any (default: "N/A" or 0)
        column_defaults: Optional[Dict[str, Any]] — Mapping of specific column -> default value
        columns: Optional[List[str]] — Columns to apply default_value to
    """

    def transform(self, dataset: Dataset) -> Dataset:
        global_default = self.config.params.get("default_value", "N/A")
        col_defaults = self.config.params.get("column_defaults", {})
        target_cols = set(self.config.params.get("columns", []))

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for k, v in new_row.items():
                if target_cols and k not in target_cols and k not in col_defaults:
                    continue
                if v is None or (isinstance(v, str) and v.strip() == ""):
                    if k in col_defaults:
                        new_row[k] = col_defaults[k]
                    else:
                        new_row[k] = global_default
            transformed_rows.append(new_row)

        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


class DropNullTransformer(Transformer):
    """Drops rows where specified key columns contain null/None values.

    Params:
        columns: List[str] — Required columns that must not be null
    """

    def transform(self, dataset: Dataset) -> Dataset:
        required_cols = self.config.params.get("columns", [])
        if not required_cols:
            return dataset

        filtered_rows = [
            row for row in dataset.rows
            if all(row.get(col) is not None and str(row.get(col)).strip() != "" for col in required_cols)
        ]
        return Dataset(schema=dataset.schema_def, rows=filtered_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


class MaskingTransformer(Transformer):
    """Masks sensitive data (e.g. phone numbers, NIK, credit cards, emails).

    Params:
        columns: List[str] — Target columns to mask
        mask_char: str — Character used for masking (default '*')
        keep_start: int — Number of characters to leave unmasked at start (default 2)
        keep_end: int — Number of characters to leave unmasked at end (default 2)
    """

    def transform(self, dataset: Dataset) -> Dataset:
        target_cols = set(self.config.params.get("columns", []))
        mask_char = self.config.params.get("mask_char", "*")
        keep_start = int(self.config.params.get("keep_start", 2))
        keep_end = int(self.config.params.get("keep_end", 2))

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for col_name in target_cols:
                val = new_row.get(col_name)
                if val is not None:
                    s = str(val)
                    if len(s) <= (keep_start + keep_end):
                        new_row[col_name] = mask_char * len(s)
                    else:
                        start_part = s[:keep_start]
                        end_part = s[-keep_end:] if keep_end > 0 else ""
                        masked_len = len(s) - keep_start - keep_end
                        new_row[col_name] = f"{start_part}{mask_char * masked_len}{end_part}"
            transformed_rows.append(new_row)

        return Dataset(schema=dataset.schema_def, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


# Register with TransformationRegistry
TransformationRegistry.register("fill_null", FillNullTransformer)
TransformationRegistry.register("drop_null", DropNullTransformer)
TransformationRegistry.register("mask", MaskingTransformer)
