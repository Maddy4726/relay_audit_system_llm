"""Relay audit system CLI — extract relay feeder test reports from DOCX to JSON."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from relay_audit_system.extraction import (
    ConfigurationError,
    DocxLoadError,
    ExtractionError,
    extract_docx_to_json,
)
from relay_audit_system.extraction.exceptions import RelayAuditError
from relay_audit_system.utils.config import load_settings
from relay_audit_system.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract industrial relay feeder test report data from DOCX to JSON.",
    )
    parser.add_argument(
        "docx_path",
        type=Path,
        help="Path to the input .docx report (absolute or relative).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: extracted_json/<stem>.json).",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Resolve relative DOCX paths against this directory (default: input_docs/).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    args = _parse_args(argv)
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        settings = load_settings()
    except ConfigurationError as exc:
        logger.error("Configuration error: %s", exc)
        return 2

    docx_path = args.docx_path
    if not docx_path.is_absolute():
        input_dir = args.input_dir or settings.input_docs_dir
        docx_path = input_dir / docx_path

    try:
        output = extract_docx_to_json(
            docx_path,
            output_path=args.output,
            settings=settings,
        )
    except ConfigurationError as exc:
        logger.error("Configuration error: %s", exc)
        return 2
    except DocxLoadError as exc:
        logger.error("DOCX load error: %s", exc)
        return 3
    except ExtractionError as exc:
        logger.error("Extraction error: %s", exc)
        return 4
    except RelayAuditError as exc:
        logger.error("Pipeline error: %s", exc)
        return 5
    except Exception:
        logger.exception("Unexpected failure during extraction")
        return 1

    logger.info("Extraction complete: %s", output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
