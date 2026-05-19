"""Relay audit system — batch extraction runner for relay feeder test reports."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

from relay_audit_system.extraction import (
    ConfigurationError,
    DocxLoadError,
    ExtractionError,
    extract_docx_to_json,
)
from relay_audit_system.extraction.exceptions import RelayAuditError
from relay_audit_system.utils.config import Settings, load_settings
from relay_audit_system.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FileExtractionResult:
    """Outcome of extracting a single DOCX file."""

    source: Path
    output: Path | None = None
    success: bool = False
    error: str | None = None


@dataclass(slots=True)
class BatchExtractionSummary:
    """Aggregated results for a batch extraction run."""

    input_dir: Path
    output_dir: Path
    results: list[FileExtractionResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> list[FileExtractionResult]:
        return [r for r in self.results if r.success]

    @property
    def failed(self) -> list[FileExtractionResult]:
        return [r for r in self.results if not r.success]

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)


def discover_docx_files(input_dir: Path) -> list[Path]:
    """
    Find all ``.docx`` files in ``input_dir`` (non-recursive).

    Returns:
        Sorted list of DOCX paths.

    Raises:
        FileNotFoundError: If the input directory does not exist.
    """
    directory = Path(input_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Input directory not found: {directory}")

    files = sorted(
        path.resolve()
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".docx" and not path.name.startswith("~$")
    )
    logger.info("Discovered %d DOCX file(s) in %s", len(files), directory)
    return files


def extract_single_file(
    docx_path: Path,
    *,
    settings: Settings,
    output_dir: Path | None = None,
) -> FileExtractionResult:
    """
    Run the extraction pipeline for one DOCX file.

    Errors are captured and returned instead of raised.
    """
    source = Path(docx_path).resolve()
    out_dir = Path(output_dir or settings.extracted_json_dir)
    result = FileExtractionResult(source=source)

    try:
        destination = out_dir / f"{source.stem}.json"
        output = extract_docx_to_json(
            source,
            output_path=destination,
            settings=settings,
        )
        result.output = Path(output).resolve()
        result.success = True
        logger.info("Extracted %s -> %s", source.name, result.output.name)
    except (DocxLoadError, ExtractionError, RelayAuditError) as exc:
        result.error = str(exc)
        logger.error("Failed to extract %s: %s", source.name, exc)
    except Exception as exc:
        result.error = f"Unexpected error: {exc}"
        logger.exception("Unexpected failure extracting %s", source.name)

    return result


def run_batch_extraction(
    *,
    settings: Settings,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> BatchExtractionSummary:
    """
    Extract all DOCX files from ``input_dir`` and save JSON to ``output_dir``.

    Returns:
        Summary with per-file success and failure details.
    """
    in_dir = Path(input_dir or settings.input_docs_dir).resolve()
    out_dir = Path(output_dir or settings.extracted_json_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = BatchExtractionSummary(input_dir=in_dir, output_dir=out_dir)

    try:
        docx_files = discover_docx_files(in_dir)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return summary

    if not docx_files:
        logger.warning("No DOCX files found in %s", in_dir)
        return summary

    for docx_path in docx_files:
        result = extract_single_file(docx_path, settings=settings, output_dir=out_dir)
        summary.results.append(result)

    return summary


def print_extraction_summary(summary: BatchExtractionSummary) -> None:
    """Print a human-readable batch extraction summary to stdout."""
    width = 72
    print()
    print("=" * width)
    print("RELAY AUDIT EXTRACTION SUMMARY")
    print("=" * width)
    print(f"Input directory:  {summary.input_dir}")
    print(f"Output directory: {summary.output_dir}")
    print(f"Total files:      {summary.total}")
    print(f"Succeeded:        {summary.success_count}")
    print(f"Failed:           {summary.failure_count}")
    print("-" * width)

    if summary.succeeded:
        print("\nSuccessful extractions:")
        for item in summary.succeeded:
            print(f"  [OK]   {item.source.name}")
            print(f"         -> {item.output}")

    if summary.failed:
        print("\nFailed extractions:")
        for item in summary.failed:
            print(f"  [FAIL] {item.source.name}")
            print(f"         {item.error}")

    if summary.total == 0:
        print("\nNo DOCX files were processed.")

    print("=" * width)
    print()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-extract relay feeder test reports from DOCX files to JSON.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing .docx reports (default: input_docs/).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for extracted JSON files (default: extracted_json/).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Process a single .docx file instead of the full input directory.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(argv)


def _exit_code_for_summary(summary: BatchExtractionSummary) -> int:
    if summary.total == 0:
        return 0
    if summary.failure_count == 0:
        return 0
    if summary.success_count == 0:
        return 4
    return 3  # partial failure


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    args = _parse_args(argv)
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        settings = load_settings()
    except ConfigurationError as exc:
        logger.error("Configuration error: %s", exc)
        return 2

    if args.file is not None:
        docx_path = Path(args.file)
        if not docx_path.is_absolute():
            docx_path = Path(args.input_dir or settings.input_docs_dir) / docx_path
        if not docx_path.is_file():
            logger.error("File not found: %s", docx_path)
            return 3

        out_dir = Path(args.output_dir or settings.extracted_json_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = BatchExtractionSummary(
            input_dir=docx_path.parent,
            output_dir=out_dir,
            results=[extract_single_file(docx_path, settings=settings, output_dir=out_dir)],
        )
    else:
        summary = run_batch_extraction(
            settings=settings,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )

    print_extraction_summary(summary)
    return _exit_code_for_summary(summary)


if __name__ == "__main__":
    sys.exit(main())
