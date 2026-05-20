"""
Safely create or update relay_audit_system/.env without printing the API key.

Usage:
    PYTHONPATH=. python -m relay_audit_system.tools.setup_env
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PACKAGE_ROOT / ".env"
EXAMPLE_FILE = PACKAGE_ROOT / ".env.example"
DEFAULT_MODEL = "gpt-4.1-mini"


def _write_env(api_key: str, model: str) -> None:
    content = (
        "# Local secrets — this file is gitignored; never commit it\n"
        f"OPENAI_API_KEY={api_key}\n"
        f"OPENAI_MODEL={model}\n"
    )
    ENV_FILE.write_text(content, encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass  # Windows may not support chmod


def main() -> int:
    if ENV_FILE.is_file():
        answer = input(f"{ENV_FILE} already exists. Overwrite? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return 0

    print("Paste your OpenAI API key (input is hidden):")
    api_key = getpass.getpass("OPENAI_API_KEY: ").strip().strip('"').strip("'")
    if not api_key:
        print("Error: empty key.")
        return 1
    if not api_key.startswith("sk-"):
        print("Warning: key does not start with 'sk-'. Continue anyway.")

    model = input(f"Model [{DEFAULT_MODEL}]: ").strip() or DEFAULT_MODEL
    _write_env(api_key, model)
    print(f"Wrote {ENV_FILE} (permissions restricted where supported).")
    print("Run: PYTHONPATH=. python -m relay_audit_system.tools.verify_api")
    return 0


if __name__ == "__main__":
    sys.exit(main())
