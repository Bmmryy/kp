"""Cast Columns Transformer for FlowETL.

Memungkinkan konversi tipe data kolom secara eksplisit berdasarkan mapping
{column_name: target_type} yang ditentukan pengguna. Berguna saat source file
(CSV/JSON) dimasukkan ke SQL dan user ingin override tipe inferensi otomatis.
"""

from typing import Any, Dict

from app.schema.casting import cast_value
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry
from app.utils.logging import get_logger

logger = get_logger("flowetl.transformations.casting")


class CastColumnsTransformer(Transformer):
    """Mengubah tipe data kolom-kolom dataset berdasarkan mapping yang diberikan.

    Params:
        column_types: Dict[str, str] — Mapping nama kolom ke tipe data canonical
            (string/integer/float/decimal/boolean/date/datetime/time/json/binary).
            Contoh: {"age": "integer", "salary": "decimal", "is_active": "boolean"}
    """

    def _get_column_types(self) -> Dict[str, DataType]:
        """Baca dan validasi mapping kolom → DataType dari config."""
        raw: Dict[str, str] = self.config.params.get("column_types", {})
        result: Dict[str, DataType] = {}
        for col_name, type_str in raw.items():
            try:
                result[col_name] = DataType.from_str(type_str)
            except ValueError:
                logger.warning(
                    "CastColumnsTransformer: tipe '%s' untuk kolom '%s' tidak dikenal, diabaikan.",
                    type_str,
                    col_name,
                )
        return result

    def transform(self, dataset: Dataset) -> Dataset:
        col_type_map = self._get_column_types()
        if not col_type_map:
            return dataset

        transformed_rows = []
        for row in dataset.rows:
            new_row = dict(row)
            for col_name, target_type in col_type_map.items():
                if col_name in new_row:
                    raw_val = new_row[col_name]
                    try:
                        new_row[col_name] = cast_value(raw_val, target_type)
                    except Exception as exc:
                        logger.debug(
                            "CastColumnsTransformer: gagal cast '%s' kolom '%s' → %s: %s. Nilai asli dipertahankan.",
                            raw_val,
                            col_name,
                            target_type.value,
                            exc,
                        )
                        # Biarkan nilai asli jika cast gagal (graceful)
            transformed_rows.append(new_row)

        # Update schema untuk mencerminkan tipe baru
        new_schema = self.get_output_schema(dataset.schema_def)
        return Dataset(schema=new_schema, rows=transformed_rows)

    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        col_type_map = self._get_column_types()
        if not col_type_map:
            return input_schema

        new_cols = []
        for col in input_schema.columns:
            if col.name in col_type_map:
                # Buat salinan dengan tipe baru
                updated = ColumnDefinition(
                    name=col.name,
                    data_type=col_type_map[col.name],
                    nullable=col.nullable,
                    primary_key=col.primary_key,
                    unique=col.unique,
                    default=col.default,
                    metadata=dict(col.metadata),
                )
                new_cols.append(updated)
            else:
                new_cols.append(col)

        return TableSchema(name=input_schema.name, columns=new_cols)


# Register with TransformationRegistry
TransformationRegistry.register("cast_columns", CastColumnsTransformer)
