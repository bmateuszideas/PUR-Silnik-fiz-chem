"""Logging helpers for PUR-MOLD-TWIN."""

from __future__ import annotations

import logging
from typing import Optional

LOGGER_NAME = "pur_mold_twin"
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure root logger and return the project logger."""

    numeric_level = _normalize_level(level)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=numeric_level, format=DEFAULT_FORMAT)
    root_logger.setLevel(numeric_level)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(numeric_level)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger scoped to the provided name."""

    return logging.getLogger(name or LOGGER_NAME)


def _normalize_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return logging._nameToLevel.get(level.upper(), logging.INFO)
    return logging.INFO
