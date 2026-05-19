"""Extraction pipeline exceptions."""


class RelayAuditError(Exception):
    """Base error for relay audit extraction."""


class ConfigurationError(RelayAuditError):
    """Missing or invalid configuration."""


class DocxLoadError(RelayAuditError):
    """Failed to read or parse a DOCX file."""


class ExtractionError(RelayAuditError):
    """OpenAI extraction or structured output parsing failed."""
