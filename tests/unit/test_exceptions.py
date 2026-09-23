"""Unit tests for FlowETL domain exception hierarchy."""

from app.core.exceptions import (
    ConfigurationError,
    ConnectionFailedError,
    ConnectorError,
    FlowETLError,
    LoadError,
    PipelineExecutionError,
    TransformationError,
)


def test_exception_inheritance():
    assert issubclass(ConnectorError, FlowETLError)
    assert issubclass(ConnectionFailedError, ConnectorError)
    assert issubclass(LoadError, ConnectorError)
    assert issubclass(TransformationError, FlowETLError)
    assert issubclass(ConfigurationError, FlowETLError)


def test_user_friendly_formatting():
    err = ConnectionFailedError(
        message="Unable to connect to MySQL database at localhost:3306.",
        details="Access denied for user 'root'@'localhost' (using password: YES)",
        suggested_action="Verify database host, port, username, and password in connection settings.",
    )
    formatted = err.to_user_friendly_string()
    assert "Unable to connect to MySQL database at localhost:3306." in formatted
    assert "Access denied for user 'root'@'localhost'" in formatted
    assert "Suggested action:" in formatted
    assert "Verify database host" in formatted
