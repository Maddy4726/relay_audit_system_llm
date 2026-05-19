"""Logging setup for the relay audit extraction pipeline."""

from __future__ import annotations

import logging
import sys


def setup_logging(*, level: int = logging.INFO) -> None:
    """Configure root logger once for CLI and library use."""
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)
