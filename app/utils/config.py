"""Pipeline & Application Configuration Loader for FlowETL.

Provides robust Pydantic models for validating declarative YAML/dict pipeline configurations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from app.core.exceptions import ConfigurationError


class SourceStepConfig(BaseModel):
    """Source configuration in a pipeline definition."""

    type: str = Field(..., description="Connector type (e.g. mysql, postgresql, csv)")
    connection: str = Field(..., description="Named connection or connection identifier")
    table: str = Field(..., description="Source table or file name")
    query: Optional[str] = Field(None, description="Optional custom extraction query")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional extraction options")


class DestinationStepConfig(BaseModel):
    """Destination configuration in a pipeline definition."""

    type: str = Field(..., description="Connector type (e.g. postgresql, mysql, csv)")
    connection: str = Field(..., description="Named connection or connection identifier")
    table: str = Field(..., description="Destination table or file name")
    mode: str = Field("append", description="Write mode ('append', 'replace', 'truncate')")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional loading options")


class PipelineConfig(BaseModel):
    """Declarative specification of an entire FlowETL pipeline."""

    name: str = Field(..., description="Unique pipeline identifier")
    description: Optional[str] = Field(None, description="Human-readable summary of purpose")
    source: SourceStepConfig = Field(..., description="Source configuration")
    transformations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Ordered list of transformation step definitions"
    )
    destination: DestinationStepConfig = Field(..., description="Destination target configuration")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PipelineConfig:
        """Instantiates and validates pipeline config from a dictionary."""
        try:
            return cls(**data)
        except Exception as err:
            raise ConfigurationError(
                f"Failed to validate pipeline configuration: {err}",
                details=str(err),
                suggested_action="Check the structure of your pipeline configuration fields.",
            )

    @classmethod
    def from_yaml_file(cls, file_path: str | Path) -> PipelineConfig:
        """Loads and validates a pipeline YAML file."""
        path = Path(file_path)
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {file_path}",
                suggested_action=f"Ensure the file exists at {path.resolve()}",
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("YAML root must be a mapping/dictionary.")
            return cls.from_dict(data)
        except yaml.YAMLError as err:
            raise ConfigurationError(
                f"Invalid YAML syntax in {file_path}: {err}",
                details=str(err),
                suggested_action="Verify YAML indentation and syntax.",
            )
