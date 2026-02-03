"""
Axiom Design Engine - Worker Logging
Structured logging for worker processes
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

from workers.config import settings


class StructuredFormatter(logging.Formatter):
    """
    JSON structured log formatter for production.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "worker_id"):
            log_data["worker_id"] = record.worker_id

        # Add any other extra attributes
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "job_id", "task_id", "worker_id", "message",
            ):
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for development.
    """

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        
        # Build message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        
        # Add job context if available
        context = ""
        if hasattr(record, "job_id"):
            context = f"[{record.job_id[:8]}] "

        message = f"{color}{timestamp} | {level}{self.RESET} | {context}{record.getMessage()}"

        # Add extra fields
        extras = []
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "job_id", "task_id", "worker_id", "message",
            ):
                extras.append(f"{key}={value}")

        if extras:
            message += f" | {', '.join(extras)}"

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class TaskLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds task context to all log messages.
    """

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        # Merge extra with existing kwargs
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """Configure logging for worker processes."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Choose formatter based on environment
    if settings.log_level == "DEBUG":
        formatter = ColoredFormatter()
    else:
        formatter = StructuredFormatter()

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_task_logger(
    name: str,
    job_id: str | None = None,
    task_id: str | None = None,
    worker_id: str | None = None,
) -> TaskLoggerAdapter:
    """
    Get a logger with task context.
    
    Args:
        name: Logger name (usually __name__)
        job_id: Job ID for context
        task_id: Celery task ID
        worker_id: Worker hostname
        
    Returns:
        Logger adapter with context
    """
    logger = logging.getLogger(name)
    
    extra = {}
    if job_id:
        extra["job_id"] = job_id
    if task_id:
        extra["task_id"] = task_id
    if worker_id:
        extra["worker_id"] = worker_id

    return TaskLoggerAdapter(logger, extra)


# Setup logging on module import
setup_logging()
