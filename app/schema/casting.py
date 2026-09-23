"""FlowETL Value Coercion and Type Casting Engine.

Provides robust, type-safe conversions for heterogeneous tabular row values
into FlowETL canonical Python data types.
"""

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
import json
import math
from typing import Any, Optional

from app.core.exceptions import SchemaMappingError
from app.schema.models import DataType


def is_null_like(value: Any) -> bool:
    """Checks whether a value represents a null or empty state."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in ("", "null", "none", "nan", "nil", "\\n"):
            return True
    return False


def cast_value(
    value: Any,
    target_type: DataType,
    column_name: str = "unknown",
    nullable: bool = True,
) -> Any:
    """Coerces a raw Python value to match the specified canonical DataType.

    Args:
        value: Raw incoming value from source connector
        target_type: Target canonical DataType
        column_name: Column identifier for error reporting
        nullable: Whether nulls are permitted for this column

    Returns:
        Coerced typed value or None

    Raises:
        SchemaMappingError: When value cannot be converted and is not nullable
    """
    if is_null_like(value):
        if not nullable:
            raise SchemaMappingError(
                message=f"Non-nullable column '{column_name}' received a null value.",
                suggested_action=f"Provide a default value for '{column_name}' or enable nullable in schema mapping.",
            )
        return None

    try:
        if target_type == DataType.INTEGER:
            if isinstance(value, bool):
                return 1 if value else 0
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                cleaned = value.strip().replace(",", "")
                # Handle floats in strings like "123.0"
                if "." in cleaned:
                    return int(float(cleaned))
                return int(cleaned)
            return int(value)

        elif target_type == DataType.FLOAT:
            if isinstance(value, bool):
                return 1.0 if value else 0.0
            if isinstance(value, str):
                return float(value.strip().replace(",", ""))
            return float(value)

        elif target_type == DataType.DECIMAL:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            if isinstance(value, str):
                return Decimal(value.strip().replace(",", ""))
            return Decimal(value)

        elif target_type == DataType.STRING:
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value)

        elif target_type == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value != 0)
            if isinstance(value, str):
                val_lower = value.strip().lower()
                if val_lower in ("true", "t", "yes", "y", "1"):
                    return True
                elif val_lower in ("false", "f", "no", "n", "0"):
                    return False
            return bool(value)

        elif target_type == DataType.DATE:
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                # Try standard ISO formats
                cleaned = value.strip()
                if "T" in cleaned:
                    return datetime.fromisoformat(cleaned).date()
                if " " in cleaned:
                    return datetime.strptime(cleaned.split(" ")[0], "%Y-%m-%d").date()
                return date.fromisoformat(cleaned)

        elif target_type == DataType.DATETIME:
            if isinstance(value, datetime):
                return value
            if isinstance(value, date):
                return datetime.combine(value, time.min)
            if isinstance(value, str):
                cleaned = value.strip().replace("Z", "+00:00")
                if " " in cleaned and "T" not in cleaned:
                    # Common SQL timestamp format: YYYY-MM-DD HH:MM:SS
                    return datetime.fromisoformat(cleaned.replace(" ", "T"))
                return datetime.fromisoformat(cleaned)

        elif target_type == DataType.TIME:
            if isinstance(value, time):
                return value
            if isinstance(value, str):
                return time.fromisoformat(value.strip())

        elif target_type == DataType.JSON:
            if isinstance(value, (dict, list)):
                return value
            if isinstance(value, str):
                return json.loads(value.strip())
            return {"value": value}

        elif target_type == DataType.BINARY:
            if isinstance(value, bytes):
                return value
            if isinstance(value, str):
                return value.encode("utf-8")
            return bytes(value)

    except (ValueError, TypeError, InvalidOperation, json.JSONDecodeError) as err:
        raise SchemaMappingError(
            message=f"Failed to cast value '{value}' to type '{target_type.value}' in column '{column_name}'.",
            details=f"Conversion error: {err}",
            suggested_action=f"Verify that source data in column '{column_name}' contains valid {target_type.value} values.",
        ) from err

    return value
