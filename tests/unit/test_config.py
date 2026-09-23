"""Unit tests for configuration loaders and Pydantic validators."""

import pytest
from app.core.exceptions import ConfigurationError
from app.utils.config import PipelineConfig


def test_pipeline_config_from_dict():
    raw_config = {
        "name": "test_pipeline",
        "description": "Test integration pipeline",
        "source": {
            "type": "csv",
            "connection": "local_files",
            "table": "patients.csv",
        },
        "transformations": [
            {"type": "select_columns", "params": {"columns": ["id", "name"]}}
        ],
        "destination": {
            "type": "sqlite",
            "connection": "analytics_db",
            "table": "patients",
            "mode": "replace",
        },
    }
    cfg = PipelineConfig.from_dict(raw_config)
    assert cfg.name == "test_pipeline"
    assert cfg.source.type == "csv"
    assert cfg.source.table == "patients.csv"
    assert len(cfg.transformations) == 1
    assert cfg.destination.type == "sqlite"
    assert cfg.destination.mode == "replace"


def test_invalid_pipeline_config():
    # Missing destination and source
    with pytest.raises(ConfigurationError):
        PipelineConfig.from_dict({"name": "invalid_pipeline"})
