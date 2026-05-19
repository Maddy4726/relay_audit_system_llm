"""Document extraction via OpenAI Responses API."""

from relay_audit_system.extraction.engine import (
    build_extraction_prompt,
    default_json_output_path,
    extract_docx_to_json,
    extract_structured_json,
    load_docx_text,
    save_json,
)
from relay_audit_system.extraction.exceptions import (
    ConfigurationError,
    DocxLoadError,
    ExtractionError,
    RelayAuditError,
)

__all__ = [
    "ConfigurationError",
    "DocxLoadError",
    "ExtractionError",
    "RelayAuditError",
    "build_extraction_prompt",
    "default_json_output_path",
    "extract_docx_to_json",
    "extract_structured_json",
    "load_docx_text",
    "save_json",
]
