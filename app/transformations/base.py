"""Base Transformation Interface for FlowETL.

Defines the contract for all modular transformation operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel, Field

from app.schema.models import Dataset, TableSchema


class TransformerConfig(BaseModel):
    """Configuration model for a transformation step."""

    type: str = Field(..., description="Unique transformation identifier (e.g. select_columns, rename)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Step-specific arguments")


class Transformer(ABC):
    """Abstract Base Class for all FlowETL data transformations."""

    def __init__(self, config: TransformerConfig) -> None:
        self.config = config

    @abstractmethod
    def transform(self, dataset: Dataset) -> Dataset:
        """Applies transformation to the input dataset and returns the transformed dataset."""
        pass

    @abstractmethod
    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        """Computes and returns the anticipated schema resulting from this transformation."""
        pass

    def validate_input(self, dataset: Dataset) -> bool:
        """Verifies if input dataset satisfies prerequisites for this transformer."""
        return True
