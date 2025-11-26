"""Central logging configuration."""

from __future__ import annotations

import logging
import re
from logging import Logger, LogRecord

SANITIZE_PATTERN = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]")
ORIGINAL_FACTORY = logging.getLogRecordFactory()


def _sanitize(value: str) -> str:
    """Remove special characters beyond printable ASCII."""
    return SANITIZE_PATTERN.sub("", value)


def _sanitize_args(args: object) -> object:
    """Sanitize str values nested in log args."""
    if isinstance(args, tuple):
        return tuple(_sanitize(arg) if isinstance(arg, str) else arg for arg in args)
    if isinstance(args, dict):
        return {
            key: _sanitize(val) if isinstance(val, str) else val
            for key, val in args.items()
        }
    if isinstance(args, str):
        return _sanitize(args)
    return args


def _log_record_factory(*factory_args: object, **factory_kwargs: object) -> LogRecord:
    """Global sanitizing factory to cover log records created anywhere."""
    record = ORIGINAL_FACTORY(*factory_args, **factory_kwargs)
    if isinstance(record.msg, str):
        record.msg = _sanitize(record.msg)
    if record.args:
        record.args = _sanitize_args(record.args)
    return record


logging.setLogRecordFactory(_log_record_factory)


class SanitizingFormatter(logging.Formatter):
    """Strip special characters from log output for consistent terminals."""

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return SANITIZE_PATTERN.sub("", rendered)


def create_logger(name: str = "pdf_llama") -> Logger:
    """Create a console logger for pipeline scripts."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = SanitizingFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
