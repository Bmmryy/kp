"""FlowETL Structured & Contextual Logging System.

Configures formatted standard library logging and provides an in-memory
run log capture mechanism for UI display, run history, and file persistence.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import List, Optional


class FlowETLFormatter(logging.Formatter):
    """Clean, human-readable log formatter matching FlowETL specifications."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        msg = record.getMessage()
        return f"{timestamp} {level} {msg}"


class InMemoryLogHandler(logging.Handler):
    """Captures log records in memory for execution context and UI visualization."""

    def __init__(self, capacity: int = 2000) -> None:
        super().__init__()
        self.capacity = capacity
        self.records: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if len(self.records) >= self.capacity:
                self.records.pop(0)
            self.records.append(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self) -> List[str]:
        return list(self.records)

    def clear(self) -> None:
        self.records.clear()


def get_logger(name: str = "flowetl", level: int = logging.INFO) -> logging.Logger:
    """Gets or initializes a configured FlowETL logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(FlowETLFormatter())
        logger.addHandler(console_handler)

    return logger
