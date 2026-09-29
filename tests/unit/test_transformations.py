"""Unit tests for FlowETL modular transformations."""

import pytest
from app.schema.models import ColumnDefinition, DataType, Dataset, TableSchema
from app.transformations.base import TransformerConfig
from app.transformations.registry import TransformationRegistry
import app.transformations  # ensure transformers are registered


@pytest.fixture
def sample_dataset() -> Dataset:
    schema = TableSchema(
        name="test_people",
        columns=[
            ColumnDefinition(name="id", data_type=DataType.INTEGER, primary_key=True),
            ColumnDefinition(name="full_name", data_type=DataType.STRING),
            ColumnDefinition(name="city", data_type=DataType.STRING),
            ColumnDefinition(name="phone", data_type=DataType.STRING),
        ],
    )
    rows = [
        {"id": 1, "full_name": "  budi santoso  ", "city": "jakarta selatan", "phone": "081234567890"},
        {"id": 2, "full_name": "siti aminah ", "city": " bandung ", "phone": "081987654321"},
        {"id": 3, "full_name": None, "city": "", "phone": "082100000000"},
    ]
    return Dataset(schema=schema, rows=rows)


def test_trim_transformer(sample_dataset):
    cfg = TransformerConfig(type="trim", params={})
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    assert result.rows[0]["full_name"] == "budi santoso"
    assert result.rows[0]["city"] == "jakarta selatan"
    assert result.rows[1]["city"] == "bandung"
    assert result.rows[2]["full_name"] is None


def test_capitalize_transformer(sample_dataset):
    cfg = TransformerConfig(type="capitalize", params={"mode": "title"})
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    # Title case should capitalize each word
    assert "Budi Santoso" in result.rows[0]["full_name"]
    assert "Jakarta Selatan" in result.rows[0]["city"]
    assert "Bandung" in result.rows[1]["city"]


def test_trim_and_capitalize_chain(sample_dataset):
    trim_t = TransformationRegistry.create(TransformerConfig(type="trim", params={}))
    cap_t = TransformationRegistry.create(TransformerConfig(type="capitalize", params={"mode": "title"}))

    step1 = trim_t.transform(sample_dataset)
    step2 = cap_t.transform(step1)

    assert step2.rows[0]["full_name"] == "Budi Santoso"
    assert step2.rows[0]["city"] == "Jakarta Selatan"
    assert step2.rows[1]["full_name"] == "Siti Aminah"
    assert step2.rows[1]["city"] == "Bandung"


def test_fill_null_transformer(sample_dataset):
    cfg = TransformerConfig(type="fill_null", params={"default_value": "Tidak Diketahui"})
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    assert result.rows[2]["full_name"] == "Tidak Diketahui"
    assert result.rows[2]["city"] == "Tidak Diketahui"
    assert result.rows[0]["full_name"] == "  budi santoso  "


def test_drop_null_transformer(sample_dataset):
    cfg = TransformerConfig(type="drop_null", params={"columns": ["full_name"]})
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    # Row 3 had None in full_name, should be dropped
    assert len(result.rows) == 2
    assert result.rows[0]["id"] == 1
    assert result.rows[1]["id"] == 2


def test_masking_transformer(sample_dataset):
    cfg = TransformerConfig(
        type="mask",
        params={"columns": ["phone"], "mask_char": "*", "keep_start": 4, "keep_end": 3},
    )
    transformer = TransformationRegistry.create(cfg)
    result = transformer.transform(sample_dataset)

    # "081234567890" -> start 4 ("0812"), end 3 ("890"), middle masked (5 stars)
    assert result.rows[0]["phone"] == "0812*****890"
    assert result.rows[1]["phone"] == "0819*****321"
