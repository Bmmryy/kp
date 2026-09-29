"""Transformations package for FlowETL."""

from app.transformations.base import Transformer, TransformerConfig
from app.transformations.registry import TransformationRegistry
import app.transformations.text  # triggers auto-registration
import app.transformations.cleansing  # triggers auto-registration

__all__ = [
    "Transformer",
    "TransformerConfig",
    "TransformationRegistry",
]
