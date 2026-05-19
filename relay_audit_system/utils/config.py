"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent

DEFAULT_MODEL = "gpt-4.1-mini"
ENV_FILE = PACKAGE_ROOT / ".env"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for the extraction pipeline."""

    openai_api_key: str
    openai_model: str
    input_docs_dir: Path
    extracted_json_dir: Path


def load_settings(*, env_file: Path | None = ENV_FILE) -> Settings:
    """
    Load settings from ``.env`` (if present) and process environment.

    Raises:
        ConfigurationError: If required variables are missing.
    """
    from relay_audit_system.extraction.exceptions import ConfigurationError

    if env_file and env_file.is_file():
        load_dotenv(env_file)
    else:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY is not set. Add it to relay_audit_system/.env or the environment."
        )

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    input_docs = Path(os.getenv("INPUT_DOCS_DIR", PACKAGE_ROOT / "input_docs"))
    extracted_json = Path(os.getenv("EXTRACTED_JSON_DIR", PACKAGE_ROOT / "extracted_json"))

    if not input_docs.is_absolute():
        input_docs = PACKAGE_ROOT / input_docs
    if not extracted_json.is_absolute():
        extracted_json = PACKAGE_ROOT / extracted_json

    return Settings(
        openai_api_key=api_key,
        openai_model=model,
        input_docs_dir=input_docs,
        extracted_json_dir=extracted_json,
    )
