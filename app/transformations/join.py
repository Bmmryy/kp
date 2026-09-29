"""Multi-Table Dataset Join Transformer for FlowETL.

Enables combining/joining tabular datasets in memory based on key attributes
(supports INNER JOIN and LEFT JOIN across heterogeneous sources).
"""

from typing import Any, Dict, List, Optional
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry


class JoinTransformer(Transformer):
    """Joins input dataset with a secondary tabular dataset in-memory.

    Params:
        right_rows: List[Dict[str, Any]] — Rows of table B to join with.
        left_on: str — Key column name in table A.
        right_on: Optional[str] — Key column name in table B (default: same as left_on).
        join_type: str — 'inner' | 'left' (default: 'left').
        prefix_right: str — Prefix to prepend to columns from table B to prevent collisions.
    """

    def transform(self, dataset: Dataset) -> Dataset:
        right_rows: List[Dict[str, Any]] = self.config.params.get("right_rows", [])
        left_on: str = self.config.params.get("left_on", "id")
        right_on: str = self.config.params.get("right_on") or left_on
        join_type: str = self.config.params.get("join_type", "left").lower()
        prefix_right: str = self.config.params.get("prefix_right", "")

        # Index right rows by key for fast O(1) hash lookup
        lookup: Dict[Any, List[Dict[str, Any]]] = {}
        for r_row in right_rows:
            key = r_row.get(right_on)
            if key is not None:
                lookup.setdefault(str(key), []).append(r_row)

        merged_rows: List[Dict[str, Any]] = []
        for l_row in dataset.rows:
            l_key = l_row.get(left_on)
            matches = lookup.get(str(l_key)) if l_key is not None else None

            if matches:
                for match in matches:
                    combined = dict(l_row)
                    for k, v in match.items():
                        if k == right_on and left_on == right_on:
                            continue
                        dest_key = f"{prefix_right}{k}" if prefix_right else k
                        combined[dest_key] = v
                    merged_rows.append(combined)
            elif join_type == "left":
                # Left join: preserve left row with None for right columns
                combined = dict(l_row)
                if right_rows:
                    sample_right = right_rows[0]
                    for k in sample_right.keys():
                        if k != right_on:
                            dest_key = f"{prefix_right}{k}" if prefix_right else k
                            combined[dest_key] = None
                merged_rows.append(combined)

        out_name = f"{dataset.schema_def.name}_joined"
        if merged_rows:
            return Dataset.infer_from_dicts(out_name, merged_rows)
        return Dataset(schema=dataset.schema_def, rows=[])

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        return input_schema


# Register in TransformationRegistry
TransformationRegistry.register("join", JoinTransformer)
