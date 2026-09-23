"""Unit tests for value coercion and type casting."""

from datetime import date, datetime
from decimal import Decimal
import pytest

from app.core.exceptions import SchemaMappingError
from app.schema.casting import cast_value, is_null_like
from app.schema.models import DataType


class TestCasting:
    def test_null_like_detection(self):
        assert is_null_like(None) is True
        assert is_null_like("") is True
        assert is_null_like("  ") is True
        assert is_null_like("NULL") is True
        assert is_null_like("None") is True
        assert is_null_like("nan") is True
        assert is_null_like(0) is False
        assert is_null_like("0") is False
        assert is_null_like("valid") is False

    def test_cast_integer(self):
        assert cast_value("42", DataType.INTEGER) == 42
        assert cast_value(" 1,000 ", DataType.INTEGER) == 1000
        assert cast_value(99.0, DataType.INTEGER) == 99
        assert cast_value(True, DataType.INTEGER) == 1
        assert cast_value(False, DataType.INTEGER) == 0

    def test_cast_float_and_decimal(self):
        assert cast_value("3.1415", DataType.FLOAT) == pytest.approx(3.1415)
        assert cast_value(" 12,345.67 ", DataType.DECIMAL) == Decimal("12345.67")

    def test_cast_boolean(self):
        assert cast_value("true", DataType.BOOLEAN) is True
        assert cast_value("TRUE", DataType.BOOLEAN) is True
        assert cast_value("yes", DataType.BOOLEAN) is True
        assert cast_value("1", DataType.BOOLEAN) is True
        assert cast_value(1, DataType.BOOLEAN) is True

        assert cast_value("false", DataType.BOOLEAN) is False
        assert cast_value("0", DataType.BOOLEAN) is False
        assert cast_value("no", DataType.BOOLEAN) is False
        assert cast_value(0, DataType.BOOLEAN) is False

    def test_cast_date_and_datetime(self):
        d = cast_value("2026-09-23", DataType.DATE)
        assert d == date(2026, 9, 23)

        dt = cast_value("2026-09-23 14:30:00", DataType.DATETIME)
        assert dt == datetime(2026, 9, 23, 14, 30, 0)

        dt_iso = cast_value("2026-09-23T14:30:00", DataType.DATETIME)
        assert dt_iso == datetime(2026, 9, 23, 14, 30, 0)

    def test_cast_json(self):
        parsed = cast_value('{"patient_id": 101, "admitted": true}', DataType.JSON)
        assert isinstance(parsed, dict)
        assert parsed["patient_id"] == 101
        assert parsed["admitted"] is True

    def test_non_nullable_violation(self):
        with pytest.raises(SchemaMappingError) as exc_info:
            cast_value(None, DataType.INTEGER, column_name="patient_id", nullable=False)
        assert "Non-nullable column 'patient_id' received a null value" in exc_info.value.message

    def test_invalid_value_cast_failure(self):
        with pytest.raises(SchemaMappingError) as exc_info:
            cast_value("not_a_number", DataType.INTEGER, column_name="age")
        assert "Failed to cast value 'not_a_number' to type 'integer'" in exc_info.value.message
