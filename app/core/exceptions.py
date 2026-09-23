"""FlowETL Domain Exception Hierarchy.

Provides user-friendly, structured exceptions with diagnostic context
and actionable suggestions, preventing raw technical tracebacks from
confusing end users while preserving technical details for logging.
"""

from typing import Any, Optional


class FlowETLError(Exception):
    """Base exception for all FlowETL domain errors."""

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        suggested_action: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggested_action = suggested_action
        self.context = context or {}

    def to_user_friendly_string(self) -> str:
        """Formats the exception into a clean, human-readable notification."""
        lines = [self.message]
        if self.details:
            lines.append(f"\nDetails:\n{self.details}")
        if self.suggested_action:
            lines.append(f"\nSuggested action:\n{self.suggested_action}")
        return "\n".join(lines)

    def __str__(self) -> str:
        msg = self.message
        if self.suggested_action:
            msg += f" (Action: {self.suggested_action})"
        return msg


# Configuration & Initialization Errors
class ConfigurationError(FlowETLError):
    """Raised when pipeline configuration is invalid or missing required keys."""
    pass


# Connector Errors
class ConnectorError(FlowETLError):
    """Base error for connector operations."""
    pass


class ConnectionFailedError(ConnectorError):
    """Raised when unable to establish a connection to the data source or destination."""
    pass


class SchemaDiscoveryError(ConnectorError):
    """Raised when schema extraction fails for a given dataset or table."""
    pass


class ExtractionError(ConnectorError):
    """Raised when reading or querying data from the source fails."""
    pass


class LoadError(ConnectorError):
    """Raised when writing data to the destination fails."""
    pass


# Transformation Errors
class TransformationError(FlowETLError):
    """Raised when data transformation cannot be applied."""
    pass


# Schema Mapping Errors
class SchemaMappingError(FlowETLError):
    """Raised when type conversion or schema alignment fails."""
    pass


# Validation Errors
class ValidationError(FlowETLError):
    """Raised when data fails quality, null, type, or constraint validations."""
    pass


# Pipeline Execution Errors
class PipelineExecutionError(FlowETLError):
    """Raised during orchestrator execution lifecycle failures."""
    pass
