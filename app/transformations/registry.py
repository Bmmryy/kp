"""Transformation Registry for FlowETL.

Maintains registry mappings of transformation step types to concrete Transformer classes.
"""

from typing import Dict, List, Type
from app.core.exceptions import ConfigurationError
from app.transformations.base import Transformer, TransformerConfig


class TransformationRegistry:
    """Registry for pluggable Transformer implementations."""

    _transformers: Dict[str, Type[Transformer]] = {}

    @classmethod
    def register(cls, transform_type: str, transformer_cls: Type[Transformer]) -> None:
        cls._transformers[transform_type.lower()] = transformer_cls

    @classmethod
    def get_class(cls, transform_type: str) -> Type[Transformer]:
        key = transform_type.lower()
        if key not in cls._transformers:
            raise ConfigurationError(
                f"Transformation type '{transform_type}' is not registered.",
                suggested_action=f"Available transformations: {cls.list_available()}",
            )
        return cls._transformers[key]

    @classmethod
    def create(cls, config: TransformerConfig) -> Transformer:
        transformer_cls = cls.get_class(config.type)
        return transformer_cls(config)

    @classmethod
    def list_available(cls) -> List[str]:
        return sorted(list(cls._transformers.keys()))
