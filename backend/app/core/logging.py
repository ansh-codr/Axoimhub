"""
Axiom Design Engine - Logging Configuration
Structured logging setup with JSON formatting for production
"""

import logging
import sys
from typing import Any

import orjson
from datetime import datetime, timezone

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    Outputs logs in JSON format for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "taskName",
                "message",
            ):
                log_data[key] = value

        return orjson.dumps(log_data).decode("utf-8")


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable log formatter for development.
    Includes colors for different log levels.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Base message
        message = f"{color}{timestamp} | {record.levelname:8} | {record.name} | {record.getMessage()}{self.RESET}"

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging() -> None:
    """
    Configure application logging based on environment.
    Uses JSON formatting in production, human-readable in development.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choose formatter based on environment
    if settings.is_production:
        formatter = JSONFormatter()
    else:
        formatter = DevelopmentFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.db_echo else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ of the module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log messages.
    Useful for adding request-specific data like user_id, job_id, etc.
    """

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        # Add extra context to the log record
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_context_logger(
    name: str,
    **context: Any,
) -> LoggerAdapter:
    """
    Get a logger with additional context attached to all messages.

    Args:
        name: Logger name
        **context: Key-value pairs to attach to all log messages

    Returns:
        LoggerAdapter with context

    Example:
        logger = get_context_logger(__name__, user_id="123", job_id="456")
        logger.info("Processing job")  # Logs include user_id and job_id
    """
    base_logger = get_logger(name)
    return LoggerAdapter(base_logger, context)
